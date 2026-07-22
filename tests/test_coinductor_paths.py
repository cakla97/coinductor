import sys

from coinductor.paths import bootstrap_data_dir, resolve_data_dir


def test_resolve_data_dir_returns_none_outside_frozen_build(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)

    assert resolve_data_dir() is None


def test_resolve_data_dir_honors_explicit_override(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("COINDUCTOR_DATA_DIR", str(tmp_path / "custom"))

    assert resolve_data_dir() == tmp_path / "custom"


def test_resolve_data_dir_falls_back_to_local_appdata(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delenv("COINDUCTOR_DATA_DIR", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert resolve_data_dir() == tmp_path / "Coinductor"


def test_resolve_data_dir_falls_back_to_home_without_local_appdata(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delenv("COINDUCTOR_DATA_DIR", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    from pathlib import Path

    assert resolve_data_dir() == Path.home() / ".coinductor"


def test_bootstrap_data_dir_creates_expected_layout(tmp_path):
    data_dir = tmp_path / "Coinductor"

    bootstrap_data_dir(data_dir)

    assert (data_dir / "state").is_dir()
    assert (data_dir / "work").is_dir()
    assert (data_dir / "outputs" / "reports").is_dir()
    assert (data_dir / "research" / "notes").is_dir()
    assert (data_dir / "research" / "requests").is_dir()


def test_bootstrap_data_dir_copies_config_template_from_bundled_root(monkeypatch, tmp_path):
    bundled_root = tmp_path / "bundle"
    bundled_root.mkdir()
    (bundled_root / "config.example.toml").write_text("[app]\nmode = 'MOCK'\n", encoding="utf-8")
    monkeypatch.setattr(sys, "_MEIPASS", str(bundled_root), raising=False)

    data_dir = tmp_path / "Coinductor"
    bootstrap_data_dir(data_dir)

    target = data_dir / "config.example.toml"
    assert target.exists()
    assert "mode = 'MOCK'" in target.read_text(encoding="utf-8")


def test_bootstrap_data_dir_never_overwrites_existing_config(monkeypatch, tmp_path):
    bundled_root = tmp_path / "bundle"
    bundled_root.mkdir()
    (bundled_root / "config.example.toml").write_text("[app]\nmode = 'MOCK'\n", encoding="utf-8")
    monkeypatch.setattr(sys, "_MEIPASS", str(bundled_root), raising=False)

    data_dir = tmp_path / "Coinductor"
    data_dir.mkdir()
    target = data_dir / "config.example.toml"
    target.write_text("[app]\nmode = 'LIVE'\n", encoding="utf-8")

    bootstrap_data_dir(data_dir)

    assert "mode = 'LIVE'" in target.read_text(encoding="utf-8")
