from trading_agent.grid_registry import GridRegistry
from trading_agent.rebalancing_registry import RebalancingRegistry

from coinductor.strategy_registration import StrategyRegistrationService


def _service(tmp_path, monkeypatch) -> StrategyRegistrationService:
    monkeypatch.chdir(tmp_path)
    state_path = (tmp_path / "state" / "active.toml").as_posix()
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f"""
[app]
active_strategies_path = "{state_path}"

[grid_bot]
allowed_symbols = ["BTCUSDC", "ETHUSDC"]
min_grid_count = 8
max_grid_count = 40
max_active_grid_bots = 1

[rebalancing_bot]
allowed_assets = ["BTC", "ETH", "SOL"]
min_assets = 2
""".strip(),
        encoding="utf-8",
    )
    return StrategyRegistrationService(config_path)


def _register_grid(service: StrategyRegistrationService, *, verified: bool = True):
    return service.register_grid(
        name="BTC range bot",
        binance_bot_id="grid-123",
        symbol="BTCUSDC",
        range_low="90000",
        range_high="115000",
        grid_count="10",
        grid_type="ARITHMETIC",
        investment="250",
        entry_price="100000",
        stop_loss="88000",
        take_profit="118000",
        created_at="2026-07-10T12:00:00+02:00",
        notes="UI registration test",
        verified=verified,
    )


def test_grid_registration_requires_explicit_verification(tmp_path, monkeypatch) -> None:
    service = _service(tmp_path, monkeypatch)

    result = _register_grid(service, verified=False)

    assert result.success is False
    assert "Confirm" in result.message
    assert not (tmp_path / "state" / "active.toml").exists()


def test_registers_grid_and_rebalancing_with_shared_state(tmp_path, monkeypatch) -> None:
    service = _service(tmp_path, monkeypatch)

    grid_result = _register_grid(service)
    rebalancing_result = service.register_rebalancing(
        name="Core basket",
        binance_bot_id="reb-456",
        assets="BTC, ETH, SOL",
        target_weights="50, 25, 25",
        entry_prices="100000, 3000, 150",
        investment="300",
        threshold="10",
        created_at="",
        notes="UI registration test",
        verified=True,
    )

    config = service._config()
    grids = GridRegistry(config).list_bots()
    rebalancing = RebalancingRegistry(config).list_bots()
    assert grid_result.success is True
    assert rebalancing_result.success is True
    assert grids[0].name == "BTC range bot"
    assert grids[0].status == "ACTIVE"
    assert rebalancing[0].assets == ("BTC", "ETH", "SOL")
    assert tuple(str(item) for item in rebalancing[0].target_weights_pct) == ("50", "25", "25")


def test_registration_surfaces_registry_validation_as_user_message(tmp_path, monkeypatch) -> None:
    service = _service(tmp_path, monkeypatch)

    result = service.register_grid(
        name="Invalid range",
        binance_bot_id="grid-invalid",
        symbol="BTCUSDC",
        range_low="115000",
        range_high="90000",
        grid_count="10",
        grid_type="ARITHMETIC",
        investment="250",
        entry_price="100000",
        stop_loss="88000",
        take_profit="118000",
        created_at="",
        notes="",
        verified=True,
    )

    assert result.success is False
    assert "lower range" in result.message


def test_local_status_update_requires_binance_confirmation_and_preserves_record(tmp_path, monkeypatch) -> None:
    service = _service(tmp_path, monkeypatch)
    assert _register_grid(service).success is True

    rejected = service.update_status(
        strategy_type="Spot Grid",
        name="BTC range bot",
        status="Paused",
        verified=False,
    )
    updated = service.update_status(
        strategy_type="Spot Grid",
        name="BTC range bot",
        status="Paused",
        verified=True,
    )

    bots = GridRegistry(service._config()).list_bots()
    assert rejected.success is False
    assert updated.success is True
    assert bots[0].status == "PAUSED"
    assert service.registered_count() == 0
