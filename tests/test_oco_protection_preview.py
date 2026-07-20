from decimal import Decimal

from trading_agent.binance_client import BinanceApiError
from trading_agent.models import Balance, LivePositionCycle, LivePositionSummary, SymbolRules
from trading_agent.oco_protection_preview import OcoProtectionPreviewBuilder


def _config(**runtime) -> dict:
    return {
        "binance": {"api_base_url": "https://api.binance.com"},
        "orders": {"use_oco_when_live": True},
        "_runtime": runtime,
    }


def _rules() -> SymbolRules:
    return SymbolRules(
        symbol="BTCUSDC",
        status="TRADING",
        base_asset="BTC",
        quote_asset="USDC",
        quote_order_qty_market_allowed=True,
        min_qty=Decimal("0.0001"),
        max_qty=Decimal("100"),
        step_size=Decimal("0.0001"),
        min_notional=Decimal("5"),
        tick_size=Decimal("0.1"),
    )


def _position(**overrides) -> LivePositionCycle:
    defaults = dict(
        intent_id="abc123def4567890",
        symbol="BTCUSDC",
        buy_order_id="1",
        sell_order_id=None,
        buy_quote=Decimal("500"),
        sell_quote=None,
        quantity=Decimal("0.01"),
        entry_price=Decimal("50000"),
        current_price=Decimal("50000"),
        current_value=Decimal("500"),
        pnl_quote=Decimal("0"),
        pnl_pct=Decimal("0"),
        stop_loss_price=Decimal("45000.13"),
        take_profit_price=Decimal("55000.37"),
        status="OPEN",
        exit_preview_status="MONITORING",
        exit_preview_reason="",
    )
    defaults.update(overrides)
    return LivePositionCycle(**defaults)


def _builder(monkeypatch, **runtime) -> OcoProtectionPreviewBuilder:
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_KEY", "live-key")
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_SECRET", "live-secret")
    monkeypatch.setenv("BINANCE_API_KEY", "read-key")
    return OcoProtectionPreviewBuilder(_config(**runtime))


def test_client_order_id_is_deterministic_and_distinct_per_leg(monkeypatch):
    builder = _builder(monkeypatch)

    list_first = builder._client_order_id("OCOL", "oco-abc123def4567890")
    list_second = builder._client_order_id("OCOL", "oco-abc123def4567890")
    above = builder._client_order_id("OCOT", "oco-abc123def4567890")
    below = builder._client_order_id("OCOS", "oco-abc123def4567890")

    assert list_first == list_second
    assert len({list_first, above, below}) == 3
    assert all(len(value) <= 36 for value in (list_first, above, below))


def test_stop_loss_rounds_toward_protective_side_while_take_profit_rounds_conservatively(monkeypatch):
    builder = _builder(monkeypatch)
    monkeypatch.setattr(builder.client, "get_symbol_rules", lambda symbol: _rules())
    balances = [Balance(asset="BTC", spot_free=Decimal("1"))]

    item = builder._preview_position(_position(), balances, existing_intents=set())

    # Raw stop_loss_price 45000.13 with tick 0.1 rounds UP to 45000.2 (more protective:
    # the SELL stop triggers earlier, at a higher price, limiting the loss).
    assert item.stop_loss_stop_price == Decimal("45000.2")
    # Raw take_profit_price 55000.37 with tick 0.1 rounds DOWN to 55000.3 (unchanged,
    # conservative: does not overstate a reachable take-profit price).
    assert item.take_profit_price == Decimal("55000.3")
    assert item.status == "READY"


def test_retrying_oco_submit_after_lost_response_reuses_same_client_order_ids(monkeypatch):
    # Regression test: mirrors the live-BUY duplicate-order fix. A network timeout after
    # Binance actually accepted the OCO list must not cause a retry to mint new client
    # order ids, or Binance's own duplicate-clientOrderId protection is defeated.
    builder = _builder(monkeypatch, oco_protection_submit=True, mainnet_oco_confirm="CONFIRM_MAINNET_OCO")
    monkeypatch.setattr(builder.client, "get_symbol_rules", lambda symbol: _rules())
    balances = [Balance(asset="BTC", spot_free=Decimal("1"))]

    seen_ids: list[tuple[str, str, str]] = []

    def fake_submit(**kwargs):
        seen_ids.append((kwargs["list_client_order_id"], kwargs["above_client_order_id"], kwargs["below_client_order_id"]))
        raise BinanceApiError("simulated network timeout")

    monkeypatch.setattr(builder.live_client, "submit_sell_oco_protection", fake_submit)

    live_positions = LivePositionSummary(
        enabled=True,
        open_positions=(_position(),),
        closed_positions=(),
        total_realized_pnl_quote=Decimal("0"),
        summary="",
    )

    first_report = builder.build(live_positions, balances)
    second_report = builder.build(live_positions, balances)

    assert first_report.items[0].status == "SUBMIT_ERROR"
    assert second_report.items[0].status == "SUBMIT_ERROR"
    assert len(seen_ids) == 2
    assert seen_ids[0] == seen_ids[1]
