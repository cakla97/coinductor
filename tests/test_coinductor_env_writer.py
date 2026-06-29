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
