from coinductor import ai_provider
from coinductor.ai_provider import AiProviderService

from test_coinductor_setup_service import VALID_CONFIG


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return b'{"data": [{"id": "qwen3:14b"}]}'


def test_ai_provider_inspect_reports_configuration_without_secrets(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    secret = "never-show-ai-key"
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "LLM_BASE_URL=http://127.0.0.1:11434/v1",
                f"LLM_API_KEY={secret}",
                "LLM_MODEL=qwen3:14b",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = AiProviderService("config.toml", ".env").inspect()
    rendered = repr(snapshot)

    assert secret not in rendered
    assert "qwen3:14b" in snapshot.summary
    assert any(item["name"] == "Privacy mode" and item["status"] == "PASS" for item in snapshot.checks)
    assert snapshot.context_sections


def test_ai_provider_health_check_uses_models_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\n",
        encoding="utf-8",
    )
    called_urls: list[str] = []

    def fake_urlopen(request, timeout):
        called_urls.append(request.full_url)
        return FakeResponse()

    monkeypatch.setattr(ai_provider.urllib.request, "urlopen", fake_urlopen)

    result = AiProviderService("config.toml", ".env").health_check()

    assert result.status == "PASS"
    assert "1 model" in result.detail
    assert called_urls == ["http://127.0.0.1:11434/v1/models"]


def test_ai_provider_health_blocks_missing_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")

    result = AiProviderService("config.toml", ".env").health_check()

    assert result.status == "BLOCK"
    assert "LLM_BASE_URL" in result.detail
