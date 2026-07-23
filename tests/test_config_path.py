from trading_agent.config import default_config_path


def test_default_config_path_prefers_local_config_toml(tmp_path, monkeypatch):
    monkeypatch.delenv("COINDUCTOR_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text("[app]\n", encoding="utf-8")
    (tmp_path / "config.example.toml").write_text("[app]\n", encoding="utf-8")

    assert default_config_path() == "config.toml"


def test_default_config_path_falls_back_to_example(tmp_path, monkeypatch):
    monkeypatch.delenv("COINDUCTOR_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.example.toml").write_text("[app]\n", encoding="utf-8")

    assert default_config_path() == "config.example.toml"


def test_default_config_path_honors_env_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text("[app]\n", encoding="utf-8")
    monkeypatch.setenv("COINDUCTOR_CONFIG", "custom.toml")

    assert default_config_path() == "custom.toml"
