from coinductor import ai_provider
from coinductor.ai_provider import AiProviderService, supports_vision_model

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
    monkeypatch.delenv("LLM_VISION_MODEL", raising=False)
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
    assert snapshot.text_model == "qwen3:14b"
    assert snapshot.vision_model == ""
    assert any(item["name"] == "Vision model" and item["status"] == "WARN" for item in snapshot.checks)
    assert any(item["name"] == "Privacy mode" and item["status"] == "PASS" for item in snapshot.checks)
    assert snapshot.context_sections


def test_ai_provider_health_check_uses_models_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_VISION_MODEL", raising=False)
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


def test_ai_provider_health_verifies_separate_text_and_vision_models(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "LLM_VISION_MODEL"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\n"
        "LLM_MODEL=qwen3:14b\n"
        "LLM_VISION_MODEL=qwen3-vl:8b\n",
        encoding="utf-8",
    )

    class VisionResponse(FakeResponse):
        def read(self) -> bytes:
            return b'{"data": [{"id": "qwen3:14b"}, {"id": "qwen3-vl:8b"}]}'

    monkeypatch.setattr(ai_provider.urllib.request, "urlopen", lambda request, timeout: VisionResponse())

    result = AiProviderService("config.toml", ".env").health_check()

    assert result.status == "PASS"
    assert "Text model ready: qwen3:14b" in result.detail
    assert "Vision model ready: qwen3-vl:8b" in result.detail


def test_ai_provider_health_blocks_unavailable_vision_model(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "LLM_VISION_MODEL"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\n"
        "LLM_MODEL=qwen3:14b\n"
        "LLM_VISION_MODEL=qwen3-vl:8b\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_provider.urllib.request, "urlopen", lambda request, timeout: FakeResponse())

    result = AiProviderService("config.toml", ".env").health_check()

    assert result.status == "BLOCK"
    assert "vision model qwen3-vl:8b was not reported" in result.detail


def test_ai_provider_health_blocks_missing_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")

    result = AiProviderService("config.toml", ".env").health_check()

    assert result.status == "BLOCK"
    assert "LLM_BASE_URL" in result.detail


def test_discover_models_lists_sorted_ids_reported_by_the_endpoint(monkeypatch) -> None:
    called_urls: list[str] = []

    class MultiModelResponse(FakeResponse):
        def read(self) -> bytes:
            return b'{"data": [{"id": "qwen3:14b"}, {"id": "qwen3-vl:8b"}, {"id": ""}]}'

    def fake_urlopen(request, timeout):
        called_urls.append(request.full_url)
        return MultiModelResponse()

    monkeypatch.setattr(ai_provider.urllib.request, "urlopen", fake_urlopen)

    result = AiProviderService().discover_models("http://127.0.0.1:11434/v1")

    assert result.status == "PASS"
    assert result.models == ("qwen3-vl:8b", "qwen3:14b")
    assert called_urls == ["http://127.0.0.1:11434/v1/models"]


def test_discover_models_blocks_on_empty_base_url() -> None:
    result = AiProviderService().discover_models("")

    assert result.status == "BLOCK"
    assert "endpoint" in result.detail.lower()


def test_discover_models_blocks_when_endpoint_reports_no_models(monkeypatch) -> None:
    class EmptyResponse(FakeResponse):
        def read(self) -> bytes:
            return b'{"data": []}'

    monkeypatch.setattr(ai_provider.urllib.request, "urlopen", lambda request, timeout: EmptyResponse())

    result = AiProviderService().discover_models("http://127.0.0.1:11434/v1")

    assert result.status == "BLOCK"
    assert "no installed models" in result.detail


def test_discover_models_blocks_and_redacts_url_on_connection_failure(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise OSError("connection refused")

    monkeypatch.setattr(ai_provider.urllib.request, "urlopen", fake_urlopen)

    result = AiProviderService().discover_models("http://127.0.0.1:11434/v1")

    assert result.status == "BLOCK"
    assert "connection refused" in result.detail


def test_vision_model_detection_is_conservative() -> None:
    assert supports_vision_model("qwen3:14b") is False
    assert supports_vision_model("qwen3-vl:8b") is True
    assert supports_vision_model("llava:13b") is True
