from decimal import Decimal

from trading_agent.binance_client import BinanceApiError
from trading_agent.live_preview import LivePreviewExecutor
from trading_agent.models import RiskDecision, SymbolRules, TradeProposal


def _config(**runtime) -> dict:
    return {
        "binance": {"api_base_url": "https://api.binance.com"},
        "live_confirm": {"enabled": True, "quote_asset": "USDC", "max_quote_amount_usdt": "50"},
        "strategy": {"allowed_symbols": ["BTCUSDC"]},
        "_runtime": runtime,
    }


def _proposal() -> TradeProposal:
    return TradeProposal(
        symbol="BTCUSDC",
        action="BUY",
        confidence=Decimal("0.8"),
        quote_amount_usdt=Decimal("25"),
        stop_loss_pct=Decimal("0.05"),
        take_profit_pct=Decimal("0.08"),
        reason="test",
    )


def _risk_decision() -> RiskDecision:
    return RiskDecision(approved=True, reason="ok", adjusted_quote_amount_usdt=Decimal("25"))


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
        tick_size=Decimal("0.01"),
    )


def _executor(monkeypatch, **runtime) -> LivePreviewExecutor:
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_KEY", "live-key")
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_SECRET", "live-secret")
    monkeypatch.setenv("BINANCE_API_KEY", "read-key")
    return LivePreviewExecutor(_config(**runtime))


def test_client_order_id_is_deterministic_for_same_symbol_and_intent(monkeypatch):
    executor = _executor(monkeypatch)

    first = executor._client_order_id("BTCUSDC", "abc123def4567890")
    second = executor._client_order_id("BTCUSDC", "abc123def4567890")

    assert first == second
    assert len(first) <= 36


def test_client_order_id_differs_by_symbol_or_intent(monkeypatch):
    executor = _executor(monkeypatch)

    assert executor._client_order_id("BTCUSDC", "abc123") != executor._client_order_id("ETHUSDC", "abc123")
    assert executor._client_order_id("BTCUSDC", "abc123") != executor._client_order_id("BTCUSDC", "def456")


def test_retrying_submit_after_lost_response_reuses_same_client_order_id(monkeypatch):
    # Regression test: a network timeout after Binance actually accepted the order must
    # not cause a retried submit to mint a brand-new clientOrderId, or Binance's own
    # duplicate-clientOrderId protection is defeated and a second real order can be placed.
    executor = _executor(monkeypatch, live_submit=True, mainnet_confirm="CONFIRM_MAINNET_ORDER")
    monkeypatch.setattr(executor.client, "get_symbol_rules", lambda symbol: _rules())
    monkeypatch.setattr(executor.client, "get_spot_free_balance", lambda asset: Decimal("100"))

    seen_client_order_ids: list[str] = []

    def fake_submit(symbol, quote_amount, client_order_id):
        seen_client_order_ids.append(client_order_id)
        raise BinanceApiError("simulated network timeout")

    monkeypatch.setattr(executor.client, "submit_market_buy_quote", fake_submit)

    first_report = executor.preview_spot_proposal(_proposal(), _risk_decision())
    second_report = executor.preview_spot_proposal(_proposal(), _risk_decision())

    assert first_report.orders[0].status == "SUBMIT_ERROR"
    assert second_report.orders[0].status == "SUBMIT_ERROR"
    assert len(seen_client_order_ids) == 2
    assert seen_client_order_ids[0] == seen_client_order_ids[1]
