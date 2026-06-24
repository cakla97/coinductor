from decimal import Decimal

from trading_agent.active_strategies import ActiveStrategiesTracker
from trading_agent.grid_registry import GridRegistry
from trading_agent.models import ActiveGridBot, ActiveRebalancingBot, MarketSnapshot
from trading_agent.rebalancing_registry import RebalancingRegistry


def _config(path, max_runtime_days: int = 14) -> dict:
    return {
        "app": {"active_strategies_path": str(path)},
        "grid_bot": {
            "allowed_symbols": ["BTCUSDC"],
            "min_grid_count": 8,
            "max_grid_count": 40,
            "max_active_grid_bots": 1,
            "max_runtime_days": max_runtime_days,
        },
        "active_strategies": {"enabled": True, "warn_near_range_pct": 5},
    }


def _bot(created_at: str = "2026-06-24T10:00:00+00:00") -> ActiveGridBot:
    return ActiveGridBot(
        name="btc-grid",
        binance_bot_id="123",
        symbol="BTCUSDC",
        range_low=Decimal("90"),
        range_high=Decimal("110"),
        grid_count=10,
        grid_type="ARITHMETIC",
        investment_usdt=Decimal("25"),
        entry_price=Decimal("100"),
        stop_loss_price=Decimal("87"),
        take_profit_price=Decimal("113"),
        created_at=created_at,
        status="ACTIVE",
        notes="test",
    )


def _snapshot(price: str) -> MarketSnapshot:
    value = Decimal(price)
    return MarketSnapshot(
        symbol="BTCUSDC",
        price=value,
        ema20=value,
        ema50=value,
        ema200=value,
        rsi14=Decimal("50"),
        atr14=Decimal("2"),
        volume_trend="flat",
        trend_regime="NEUTRAL",
    )


def test_stop_loss_breach_has_priority(tmp_path) -> None:
    config = _config(tmp_path / "active.toml")
    GridRegistry(config).register(_bot(), "CONFIRM_GRID_REGISTER")

    report = ActiveStrategiesTracker(config).evaluate([_snapshot("86")])

    assert report.grid_bots[0].state == "STOP_LOSS_BREACH"


def test_take_profit_reached(tmp_path) -> None:
    config = _config(tmp_path / "active.toml")
    GridRegistry(config).register(_bot(), "CONFIRM_GRID_REGISTER")

    report = ActiveStrategiesTracker(config).evaluate([_snapshot("114")])

    assert report.grid_bots[0].state == "TAKE_PROFIT_REACHED"


def test_runtime_expiry_is_reported(tmp_path) -> None:
    config = _config(tmp_path / "active.toml", max_runtime_days=1)
    GridRegistry(config).register(_bot("2026-01-01T00:00:00+00:00"), "CONFIRM_GRID_REGISTER")

    report = ActiveStrategiesTracker(config).evaluate([_snapshot("100")])

    assert report.grid_bots[0].state == "RUNTIME_EXPIRED"
    assert report.grid_bots[0].age_days is not None


def test_rebalancing_bot_reports_theoretical_threshold_drift(tmp_path) -> None:
    config = _config(tmp_path / "active.toml")
    config["rebalancing_bot"] = {
        "allowed_assets": ["BTC", "ETH"],
        "min_assets": 2,
    }
    bot = ActiveRebalancingBot(
        name="core-rebalance",
        binance_bot_id="rb-123",
        assets=("BTC", "ETH"),
        target_weights_pct=(Decimal("50"), Decimal("50")),
        entry_prices_usdt=(Decimal("100"), Decimal("100")),
        investment_usdt=Decimal("100"),
        threshold_pct=Decimal("5"),
        created_at="2026-06-24T10:00:00+00:00",
        status="ACTIVE",
        notes="test",
    )
    RebalancingRegistry(config).register(bot, "CONFIRM_REBALANCING_REGISTER")

    report = ActiveStrategiesTracker(config).evaluate(
        [_snapshot("100")],
        {"BTC": Decimal("120"), "ETH": Decimal("80")},
    )

    assert report.rebalancing_bots[0].state == "THRESHOLD_REACHED"
    assert report.rebalancing_bots[0].current_weights_pct == (Decimal("60.00"), Decimal("40.00"))
    assert report.rebalancing_bots[0].max_drift_pct == Decimal("10.00")
