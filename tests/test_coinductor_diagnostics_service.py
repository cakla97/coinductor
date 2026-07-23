from coinductor.diagnostics_service import DiagnosticsService


def _write_min_config(path):
    path.write_text(
        """
[app]
mode = "DRY_RUN"
mock_data = true
database_path = "work/trading_agent.sqlite3"
reports_dir = "outputs/reports"

[ai]
enabled = false

[research]
enabled = true

[strategy]
allowed_symbols = ["BTCUSDC"]
""",
        encoding="utf-8",
    )


def test_report_has_expected_sections(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "state").mkdir()
    config = tmp_path / "config.toml"
    _write_min_config(config)

    report = DiagnosticsService(config, tmp_path / ".env").generate_report()

    assert "Coinductor diagnostics bundle" in report
    assert "[System]" in report
    assert "[Setup checks]" in report
    assert "[Safety stage]" in report
    assert "[Config summary]" in report
    assert "[Run history]" in report
    assert "Mode: DRY_RUN" in report


def test_report_never_includes_secret_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "state").mkdir()
    config = tmp_path / "config.toml"
    _write_min_config(config)
    env = tmp_path / ".env"
    env.write_text(
        "BINANCE_API_KEY=SECRETKEY123\nBINANCE_API_SECRET=SUPERSECRET456\nLLM_API_KEY=llmsecret789\n",
        encoding="utf-8",
    )

    report = DiagnosticsService(config, env).generate_report()

    assert "SECRETKEY123" not in report
    assert "SUPERSECRET456" not in report
    assert "llmsecret789" not in report
    # Presence is still reported (sanitized), just not the values.
    assert "Binance read-only" in report


def test_write_bundle_creates_timestamped_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "state").mkdir()
    config = tmp_path / "config.toml"
    _write_min_config(config)

    path = DiagnosticsService(config, tmp_path / ".env").write_bundle(tmp_path / "out")

    assert path.exists()
    assert path.name.startswith("coinductor-diagnostics-")
    assert path.suffix == ".txt"
    assert "[System]" in path.read_text(encoding="utf-8")


def test_report_survives_missing_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    report = DiagnosticsService(tmp_path / "nope.toml", tmp_path / ".env").generate_report()

    assert "[Config summary]" in report
    assert "config file missing" in report
