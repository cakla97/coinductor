"""The cloud AI provider path, driven against a recording stub endpoint.

The local-Ollama path is what gets exercised by hand, so the cloud path - an
API key in an Authorization header, an https host, provider HTTP errors - is
the one that can rot unnoticed. These tests run the real request builders and
assert on what the endpoint actually received.

The stub binds 127.0.0.2 on purpose: `_is_local_endpoint` matches by hostname
against 127.0.0.1/localhost/::1, so 127.0.0.2 is classified as a cloud provider
while staying entirely on the loopback interface. No network access.
"""

from __future__ import annotations

import json
import os
import socket
import socketserver
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from coinductor.ai_provider import AiProviderService, supports_vision_model
from coinductor.assistant import _describe_provider_error, _is_local_endpoint

API_KEY = "sk-test-key-not-real"
MODEL = "gpt-4o-mini"


class _Recorder(BaseHTTPRequestHandler):
    requests: list[dict] = []
    mode = "ok"

    def log_message(self, *args):
        pass

    def _reply(self, code: int, payload: object):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        type(self).requests.append(
            {"method": "GET", "path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}}
        )
        if type(self).mode == "http_401":
            return self._reply(401, {"error": {"message": "Incorrect API key provided."}})
        self._reply(200, {"object": "list", "data": [{"id": MODEL}, {"id": "gpt-4o"}]})


class _FastServer(HTTPServer):
    """HTTPServer without the reverse-DNS lookup its server_bind does.

    socket.getfqdn() on a bare loopback address costs seconds on some machines,
    and nothing here needs the resolved name.
    """

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[0], self.server_address[1]


@pytest.fixture
def stub():
    """A stub endpoint on a free 127.0.0.2 port, torn down after the test."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.2", 0))
        port = probe.getsockname()[1]
    _Recorder.requests = []
    _Recorder.mode = "ok"
    server = _FastServer(("127.0.0.2", port), _Recorder)
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True).start()
    try:
        yield f"http://127.0.0.2:{port}/v1"
    finally:
        server.shutdown()
        server.server_close()


def _service(tmp_path, base_url, monkeypatch, key=API_KEY):
    config = tmp_path / "config.toml"
    config.write_text(
        '[app]\nmode = "DRY_RUN"\n\n[ai]\nenabled = true\n'
        'base_url_env = "LLM_BASE_URL"\napi_key_env = "LLM_API_KEY"\nmodel_env = "LLM_MODEL"\n',
        encoding="utf-8",
    )
    env = tmp_path / ".env"
    env.write_text("", encoding="utf-8")
    monkeypatch.setenv("COINDUCTOR_DISABLE_KEYCHAIN", "1")
    monkeypatch.setenv("LLM_BASE_URL", base_url)
    monkeypatch.setenv("LLM_API_KEY", key)
    monkeypatch.setenv("LLM_MODEL", MODEL)
    monkeypatch.delenv("LLM_VISION_MODEL", raising=False)
    return AiProviderService(config, env)


def test_health_check_sends_the_api_key_to_a_cloud_endpoint(tmp_path, stub, monkeypatch) -> None:
    result = _service(tmp_path, stub, monkeypatch).health_check()

    assert result.status == "PASS", result.detail
    sent = _Recorder.requests[-1]
    assert sent["path"] == "/v1/models"
    assert sent["headers"]["authorization"] == f"Bearer {API_KEY}"


def test_a_trailing_slash_does_not_double_up_in_the_path(tmp_path, stub, monkeypatch) -> None:
    result = _service(tmp_path, stub + "/", monkeypatch).health_check()

    assert result.status == "PASS", result.detail
    assert "//" not in _Recorder.requests[-1]["path"]


def test_a_rejected_key_blocks_without_echoing_the_key(tmp_path, stub, monkeypatch) -> None:
    _Recorder.mode = "http_401"

    result = _service(tmp_path, stub, monkeypatch).health_check()

    assert result.status == "BLOCK"
    assert API_KEY not in result.detail, "the API key must never reach a user-facing message"


def test_only_loopback_hosts_count_as_local() -> None:
    # reasoning_effort is sent only to local endpoints; misclassifying a cloud
    # host would put an unsupported parameter on a paid request.
    assert _is_local_endpoint("http://127.0.0.1:11434/v1")
    assert _is_local_endpoint("http://localhost:11434/v1")
    assert not _is_local_endpoint("https://api.openai.com/v1")
    assert not _is_local_endpoint("http://127.0.0.2:9911/v1")


@pytest.mark.parametrize(
    ("code", "expected"),
    [(401, "LLM_API_KEY"), (403, "not allowed"), (404, "LLM_MODEL"), (429, "Rate limit")],
)
def test_provider_http_errors_name_the_real_cause(code, expected) -> None:
    """A 401 must not be reported as a network problem: with a cloud provider a
    rejected key is the most common failure, and "connection failed" would send
    the user to debug their network instead of their key."""
    import urllib.error

    error = urllib.error.HTTPError("http://x/v1", code, "err", {}, None)

    described = _describe_provider_error(error, czech=False)

    assert str(code) in described
    assert expected in described


def test_provider_errors_are_described_in_czech_too() -> None:
    import urllib.error

    error = urllib.error.HTTPError("http://x/v1", 401, "err", {}, None)

    described = _describe_provider_error(error, czech=True)

    assert "401" in described
    assert "LLM_API_KEY" in described
    # The old copy called every provider "local", which is wrong for a cloud key.
    assert "lokální" not in described.lower()


def test_mainstream_cloud_vision_models_are_recognized() -> None:
    for model in ("gpt-4o", "gpt-4.1", "claude-sonnet-4-5", "gemini-2.0-flash"):
        assert supports_vision_model(model), model


def test_switching_to_a_local_provider_clears_the_cloud_api_key(tmp_path, monkeypatch) -> None:
    """A paid key must not survive a switch back to Ollama.

    Both wizard panels write the same LLM_* variables, and every request builder
    attaches LLM_API_KEY whenever it is set - so a leftover key would be sent as
    an Authorization header to whatever is listening on localhost.
    """
    from coinductor.secret_store import SecretStore

    monkeypatch.setenv("COINDUCTOR_DISABLE_KEYCHAIN", "1")
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    store = SecretStore(env_path=env_file)

    store.set_many({"LLM_BASE_URL": "https://api.openai.com/v1", "LLM_API_KEY": "sk-paid-key"})
    assert os.environ.get("LLM_API_KEY") == "sk-paid-key"

    store.set_many({"LLM_BASE_URL": "http://127.0.0.1:11434/v1"})
    store.clear(("LLM_API_KEY",))

    assert os.environ.get("LLM_API_KEY") is None, "key still exported to the process"
    assert "LLM_API_KEY" not in env_file.read_text(encoding="utf-8"), "key still in .env"
