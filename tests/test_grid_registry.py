from decimal import Decimal

import pytest

from trading_agent.grid_registry import GridRegistry
from trading_agent.models import ActiveGridBot


def _config(path) -> dict:
    return {
        "app": {"active_strategies_path": str(path)},
        "grid_bot": {
            "allowed_symbols": ["BTCUSDC", "ETHUSDC"],
            "min_grid_count": 8,
            "max_grid_count": 40,
            "max_active_grid_bots": 1,
        },
    }


def _bot(name: str = "btc-grid", bot_id: str = "123") -> ActiveGridBot:
    return ActiveGridBot(
        name=name,
        binance_bot_id=bot_id,
        symbol="BTCUSDC",
        range_low=Decimal("90"),
        range_high=Decimal("110"),
        grid_count=10,
        grid_type="ARITHMETIC",
        investment_usdt=Decimal("25"),
        entry_price=Decimal("100"),
        stop_loss_price=Decimal("87"),
        take_profit_price=Decimal("113"),
        created_at="2026-06-24T10:00:00+00:00",
        status="ACTIVE",
        notes="test",
    )


def test_register_requires_confirmation_and_round_trips(tmp_path) -> None:
    path = tmp_path / "active_strategies.toml"
    registry = GridRegistry(_config(path))

    assert registry.register(_bot(), "") is False
    assert not path.exists()
    assert registry.register(_bot(), "CONFIRM_GRID_REGISTER") is True

    loaded = registry.list_bots()
    assert loaded == (_bot(),)


def test_active_grid_limit_blocks_second_registration(tmp_path) -> None:
    registry = GridRegistry(_config(tmp_path / "active_strategies.toml"))
    registry.register(_bot(), "CONFIRM_GRID_REGISTER")

    issues = registry.validate_new(_bot("eth-grid", "456"))

    assert any("Active grid limit" in issue for issue in issues)


def test_status_update_requires_confirmation(tmp_path) -> None:
    registry = GridRegistry(_config(tmp_path / "active_strategies.toml"))
    registry.register(_bot(), "CONFIRM_GRID_REGISTER")

    assert registry.set_status("btc-grid", "CLOSED", "") is False
    assert registry.list_bots()[0].status == "ACTIVE"
    assert registry.set_status("btc-grid", "CLOSED", "CONFIRM_GRID_STATUS") is True
    assert registry.list_bots()[0].status == "CLOSED"


def test_invalid_stop_loss_is_rejected(tmp_path) -> None:
    registry = GridRegistry(_config(tmp_path / "active_strategies.toml"))
    invalid = ActiveGridBot(**{**_bot().__dict__, "stop_loss_price": Decimal("95")})

    with pytest.raises(ValueError):
        registry.register(invalid, "CONFIRM_GRID_REGISTER")
