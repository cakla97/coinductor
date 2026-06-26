from trading_agent.asset_policy import apply_asset_policy_overrides
from trading_agent.config import load_config


def _config() -> dict:
    return {
        "app": {"base_currency": "USDC"},
        "live_confirm": {"quote_asset": "USDC"},
        "portfolio": {
            "tracked_assets": ["BNB"],
            "asset_roles": {"BNB": "PROTECTED_UTILITY"},
        },
        "strategy": {"allowed_symbols": ["BTCUSDC"]},
        "grid_bot": {"allowed_symbols": ["BTCUSDC"], "preferred_symbols": ["BTCUSDC"]},
        "rebalancing_bot": {"allowed_assets": ["BTC"]},
        "capital_sourcing": {
            "allowed_source_assets": [],
            "protected_assets": ["BNB", "BTC"],
        },
        "dust_sourcing": {"exclude_assets": ["BNB", "BTC"]},
    }


def test_asset_policy_override_can_make_bnb_grid_candidate(tmp_path) -> None:
    overrides = tmp_path / "asset_policy_overrides.toml"
    overrides.write_text('[overrides.BNB]\nrole = "GRID_CANDIDATE"\n', encoding="utf-8")

    config = apply_asset_policy_overrides(_config(), overrides)

    assert config["portfolio"]["asset_roles"]["BNB"] == "GRID_CANDIDATE"
    assert "BNBUSDC" in config["grid_bot"]["allowed_symbols"]
    assert "BNBUSDC" in config["grid_bot"]["preferred_symbols"]
    assert "BNB" not in config["capital_sourcing"]["protected_assets"]


def test_asset_policy_override_can_make_asset_active_strategy(tmp_path) -> None:
    overrides = tmp_path / "asset_policy_overrides.toml"
    overrides.write_text('[overrides.SOL]\nrole = "ACTIVE_STRATEGY"\n', encoding="utf-8")

    config = apply_asset_policy_overrides(_config(), overrides)

    assert "SOL" in config["portfolio"]["tracked_assets"]
    assert config["portfolio"]["asset_roles"]["SOL"] == "ACTIVE_STRATEGY"
    assert "SOLUSDC" in config["strategy"]["allowed_symbols"]
    assert "SOLUSDC" in config["grid_bot"]["allowed_symbols"]
    assert "SOL" in config["rebalancing_bot"]["allowed_assets"]


def test_load_config_applies_default_override_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "state").mkdir()
    (tmp_path / "config.toml").write_text(
        """
[app]
base_currency = "USDC"
mode = "DRY_RUN"
mock_data = true
database_path = "work/test.sqlite3"
reports_dir = "outputs/reports"

[portfolio]
tracked_assets = ["BNB"]
asset_roles = { BNB = "PROTECTED_UTILITY" }

[strategy]
allowed_symbols = ["BTCUSDC"]

[grid_bot]
allowed_symbols = ["BTCUSDC"]
preferred_symbols = ["BTCUSDC"]

[rebalancing_bot]
allowed_assets = ["BTC"]

[capital_sourcing]
allowed_source_assets = []
protected_assets = ["BNB"]

[dust_sourcing]
exclude_assets = ["BNB"]
""",
        encoding="utf-8",
    )
    (tmp_path / "state" / "asset_policy_overrides.toml").write_text(
        '[overrides.BNB]\nrole = "TRADING_ALLOWED"\n',
        encoding="utf-8",
    )

    config = load_config("config.toml")

    assert config.raw["portfolio"]["asset_roles"]["BNB"] == "TRADING_ALLOWED"
    assert "BNBUSDC" in config.raw["strategy"]["allowed_symbols"]
