from coinductor.setup_service import SetupService


VALID_CONFIG = """
[app]
mode = "DRY_RUN"
mock_data = true
base_currency = "USDC"
database_path = "work/test.sqlite3"
reports_dir = "outputs/reports"
active_strategies_path = "state/active_strategies.toml"

[reports]
keep_last = 30

[retention]
keep_database_runs = 10
keep_research_requests = 10

[research]
notes_dir = "research/notes"
requests_dir = "research/requests"

[binance]
api_base_url = "https://api.binance.com"
testnet_api_base_url = "https://testnet.binance.vision"

[ai]
base_url_env = "LLM_BASE_URL"
model_env = "LLM_MODEL"

[risk]
max_trades_per_day = 1
max_daily_loss_pct = 1
max_weekly_loss_pct = 3
max_position_pct_per_asset = 10
max_total_trading_capital_pct = 20
max_risk_per_trade_pct = 0.25

[consensus]
min_rsi14 = 30
max_rsi14 = 70

[rebalancing]
target_mode = "static"
target_allocation = { BTC = 100 }
threshold_pct = 5
drift_threshold_pct = 5
min_trade_value_usdt = 10
max_trade_value_usdt_per_step = 20
max_trade_pct_per_asset = 10
min_remaining_pct_per_asset = 50
min_remaining_value_usdt_per_asset = 0

[rebalancing_bot]
mode = "THRESHOLD"
allocation_method = "CUSTOM"
auto_rebalance_mode = "BY_RATIO"
allowed_assets = ["BTC", "ETH"]
threshold_pct = 10
min_asset_value_usdt = 25
min_investment_usdt = 200
max_investment_usdt = 200
max_portfolio_pct = 20

[portfolio]
tracked_assets = ["BTC", "ETH"]
asset_roles = { BTC = "CORE", ETH = "CORE" }

[strategy]
allowed_symbols = ["BTCUSDC"]

[grid_bot]
allowed_symbols = ["BTCUSDC"]
preferred_symbols = ["BTCUSDC"]
max_grid_capital_usdt = 50
max_grid_capital_pct = 10
default_investment_usdt = 25
min_quote_per_grid_usdt = 2
min_atr_pct = 1
max_atr_pct = 10
max_abs_ema200_distance_pct = 30
max_abs_7d_return_pct = 20
suitable_score = 70
watch_score = 50
atr_range_multiplier = 2
min_rsi14 = 25
target_rsi14 = 50
max_rsi14 = 75

[capital_sourcing]
allowed_source_assets = ["ETH"]
protected_assets = ["BTC"]
max_source_value_usdt_per_run = 10
max_source_pct_per_asset = 10
max_total_source_pct_per_run = 10
min_remaining_pct_per_asset = 50
min_remaining_value_usdt_per_asset = 0

[dust_sourcing]
max_convert_value_usdt_per_run = 10
min_convert_value_usdt_per_asset = 0
max_convert_pct_per_asset = 100

[earn]
allow_locked_redeem = false
allowed_redeem_assets = ["USDC"]
auto_redeem_assets = ["USDC"]
max_redeem_per_run_usdt = 10
max_redeem_per_day_usdt = 10
max_auto_redeem_usdc_per_run = 10
min_auto_redeem_reserve_usdc = 0
redeem_type = "FAST"

[testnet_execution]
max_quote_amount_usdt = 10

[live_confirm]
quote_asset = "USDC"
max_quote_amount_usdt = 10
funding_buffer_usdt = 0
preview_only = true

[trading_bankroll]
quote_asset = "USDC"
initial_seed_usdc = 0
max_flexible_earn_draw_usdc_per_run = 10
"""


def test_setup_service_reports_credentials_without_exposing_values(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    secret = "never-display-this-value"
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                f"BINANCE_API_KEY={secret}",
                "BINANCE_API_SECRET=read-secret",
                "LLM_BASE_URL=http://127.0.0.1:11434/v1",
                "LLM_MODEL=qwen3:14b",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = SetupService("config.toml", ".env").inspect()
    rendered = repr(snapshot.checks)

    assert secret not in rendered
    assert any(
        item["name"] == "Binance read-only" and item["status"] == "PASS"
        for item in snapshot.checks
    )
    assert any(
        item["name"] == "Binance Spot Testnet" and item["status"] == "WARN"
        for item in snapshot.checks
    )
    assert any(
        item["name"] == "Local AI endpoint" and item["status"] == "PASS"
        for item in snapshot.checks
    )


def test_setup_service_blocks_missing_config(tmp_path) -> None:
    snapshot = SetupService(tmp_path / "missing.toml", tmp_path / ".env").inspect()

    assert snapshot.blocked == 1
    assert snapshot.checks[1]["name"] == "Configuration"
    assert snapshot.checks[1]["status"] == "BLOCK"
