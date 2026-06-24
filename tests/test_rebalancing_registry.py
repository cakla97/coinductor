from decimal import Decimal

import pytest

from trading_agent.grid_registry import GridRegistry
from trading_agent.models import ActiveGridBot, ActiveRebalancingBot
from trading_agent.rebalancing_registry import RebalancingRegistry


def _config(path) -> dict:
    return {
        "app": {"active_strategies_path": str(path)},
        "grid_bot": {
            "allowed_symbols": ["BTCUSDC"],
            "min_grid_count": 8,
            "max_grid_count": 40,
            "max_active_grid_bots": 1,
        },
        "rebalancing_bot": {
            "allowed_assets": ["BTC", "ETH", "SOL"],
            "min_assets": 2,
        },
    }


def _bot(name: str = "core-rebalance") -> ActiveRebalancingBot:
    return ActiveRebalancingBot(
        name=name,
        binance_bot_id="rb-123",
        assets=("BTC", "ETH", "SOL"),
        target_weights_pct=(Decimal("52.9"), Decimal("23.4"), Decimal("23.7")),
        entry_prices_usdt=(Decimal("60000"), Decimal("1800"), Decimal("70")),
        investment_usdt=Decimal("100"),
        threshold_pct=Decimal("5"),
        created_at="2026-06-24T10:00:00+00:00",
        status="ACTIVE",
        notes="test",
    )


def _grid() -> ActiveGridBot:
    return ActiveGridBot(
        name="btc-grid",
        binance_bot_id="grid-123",
        symbol="BTCUSDC",
        range_low=Decimal("50000"),
        range_high=Decimal("70000"),
        grid_count=10,
        grid_type="ARITHMETIC",
        investment_usdt=Decimal("25"),
        entry_price=Decimal("60000"),
        stop_loss_price=Decimal("48000"),
        take_profit_price=Decimal("72000"),
        created_at="2026-06-24T10:00:00+00:00",
        status="ACTIVE",
        notes="test",
    )


def test_register_requires_confirmation_and_preserves_grid_state(tmp_path) -> None:
    config = _config(tmp_path / "active.toml")
    GridRegistry(config).register(_grid(), "CONFIRM_GRID_REGISTER")
    registry = RebalancingRegistry(config)

    assert registry.register(_bot(), "") is False
    assert registry.register(_bot(), "CONFIRM_REBALANCING_REGISTER") is True
    assert registry.list_bots() == (_bot(),)
    assert GridRegistry(config).list_bots() == (_grid(),)
    GridRegistry(config).set_status("btc-grid", "CLOSED", "CONFIRM_GRID_STATUS")
    assert registry.list_bots() == (_bot(),)


def test_weights_must_sum_to_100(tmp_path) -> None:
    registry = RebalancingRegistry(_config(tmp_path / "active.toml"))
    invalid = ActiveRebalancingBot(
        **{**_bot().__dict__, "target_weights_pct": (Decimal("50"), Decimal("20"), Decimal("20"))}
    )

    with pytest.raises(ValueError):
        registry.register(invalid, "CONFIRM_REBALANCING_REGISTER")


def test_status_update_requires_confirmation(tmp_path) -> None:
    registry = RebalancingRegistry(_config(tmp_path / "active.toml"))
    registry.register(_bot(), "CONFIRM_REBALANCING_REGISTER")

    assert registry.set_status("core-rebalance", "CLOSED", "") is False
    assert registry.set_status("core-rebalance", "CLOSED", "CONFIRM_REBALANCING_STATUS") is True
    assert registry.list_bots()[0].status == "CLOSED"
