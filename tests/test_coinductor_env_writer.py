import os

from coinductor.env_writer import EnvWriter


def test_env_writer_updates_existing_keys_and_preserves_other_lines(tmp_path, monkeypatch):
    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("# comment\nBINANCE_API_KEY=old\nOTHER=value\n", encoding="utf-8")

    EnvWriter(env_path).update(
        {
            "BINANCE_API_KEY": "new",
            "BINANCE_API_SECRET": "secret",
        }
    )

    rendered = env_path.read_text(encoding="utf-8")
    assert "# comment" in rendered
    assert "OTHER=value" in rendered
    assert "BINANCE_API_KEY=new" in rendered
    assert "BINANCE_API_SECRET=secret" in rendered
    assert os.environ["BINANCE_API_KEY"] == "new"


def test_env_writer_quotes_values_with_spaces_or_hash(tmp_path):
    env_path = tmp_path / ".env"

    EnvWriter(env_path).update(
        {
            "LLM_MODEL": "model with space",
            "LLM_API_KEY": "key#part",
        }
    )

    rendered = env_path.read_text(encoding="utf-8")
    assert 'LLM_MODEL="model with space"' in rendered
    assert 'LLM_API_KEY="key#part"' in rendered


def test_env_writer_stores_optional_vision_model(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_VISION_MODEL", raising=False)
    env_path = tmp_path / ".env"

    EnvWriter(env_path).update({"LLM_VISION_MODEL": "qwen3-vl:8b"})

    assert "LLM_VISION_MODEL=qwen3-vl:8b" in env_path.read_text(encoding="utf-8")
    assert os.environ["LLM_VISION_MODEL"] == "qwen3-vl:8b"


def test_env_writer_can_store_separate_live_trading_key(tmp_path, monkeypatch):
    monkeypatch.delenv("BINANCE_LIVE_TRADE_API_KEY", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("BINANCE_API_KEY=readonly\n", encoding="utf-8")

    EnvWriter(env_path).update(
        {
            "BINANCE_LIVE_TRADE_API_KEY": "live-key",
            "BINANCE_LIVE_TRADE_API_SECRET": "live-secret",
        }
    )

    rendered = env_path.read_text(encoding="utf-8")
    assert "BINANCE_API_KEY=readonly" in rendered
    assert "BINANCE_LIVE_TRADE_API_KEY=live-key" in rendered
    assert "BINANCE_LIVE_TRADE_API_SECRET=live-secret" in rendered
    assert os.environ["BINANCE_LIVE_TRADE_API_KEY"] == "live-key"
