from __future__ import annotations

import os
from decimal import Decimal

from .binance_client import BinanceApiError, BinanceClient
from .models import LiveOrderPreview, LivePreviewReport, RiskDecision, SymbolRules, TradeProposal


class LivePreviewExecutor:
    def __init__(self, config: dict):
        self.config = config
        self.client = BinanceClient(config, credential_profile="live_trade")

    def preview_spot_proposal(self, proposal: TradeProposal, risk_decision: RiskDecision) -> LivePreviewReport:
        live_config = self.config.get("live_confirm", {})
        enabled = bool(live_config.get("enabled", False))
        if not enabled:
            return LivePreviewReport(enabled=False, orders=(), summary="LIVE_CONFIRM preview is disabled.")
        if not risk_decision.approved:
            return LivePreviewReport(enabled=True, orders=(), summary="No live preview because risk engine rejected the proposal.")
        if proposal.action != "BUY":
            return LivePreviewReport(enabled=True, orders=(), summary=f"LIVE_CONFIRM preview for {proposal.action} is not implemented yet.")

        key_check = self._key_check()
        quote_amount = min(
            risk_decision.adjusted_quote_amount_usdt,
            Decimal(str(live_config.get("max_quote_amount_usdt", "10"))),
        )
        if key_check is not None:
            return LivePreviewReport(
                enabled=True,
                orders=(
                    LiveOrderPreview(
                        symbol=proposal.symbol,
                        side=proposal.action,
                        order_type="MARKET",
                        quote_amount_usdt=quote_amount,
                        status="BLOCKED",
                        validation_summary=key_check,
                        available_usdt=Decimal("0"),
                        confirmation_required="CONFIRM_MAINNET_ORDER",
                    ),
                ),
                summary="LIVE_CONFIRM preview is blocked by key guard.",
            )

        try:
            rules = self.client.get_symbol_rules(proposal.symbol)
            available_usdt = self.client.get_spot_free_balance("USDT")
            validation = self._validate_market_buy(proposal.symbol, quote_amount, rules, available_usdt)
        except BinanceApiError as exc:
            return LivePreviewReport(
                enabled=True,
                orders=(
                    LiveOrderPreview(
                        symbol=proposal.symbol,
                        side=proposal.action,
                        order_type="MARKET",
                        quote_amount_usdt=quote_amount,
                        status="BLOCKED",
                        validation_summary=str(exc),
                        available_usdt=Decimal("0"),
                        confirmation_required="CONFIRM_MAINNET_ORDER",
                    ),
                ),
                summary="LIVE_CONFIRM preview is blocked by Binance API validation.",
            )

        status = "PREVIEW_READY" if validation.startswith("OK:") else "BLOCKED"
        return LivePreviewReport(
            enabled=True,
            orders=(
                LiveOrderPreview(
                    symbol=proposal.symbol,
                    side=proposal.action,
                    order_type="MARKET",
                    quote_amount_usdt=quote_amount,
                    status=status,
                    validation_summary=validation,
                    available_usdt=available_usdt,
                    confirmation_required="CONFIRM_MAINNET_ORDER",
                ),
            ),
            summary=f"LIVE_CONFIRM preview for {proposal.symbol}: {status}. No mainnet order was submitted.",
        )

    def _key_check(self) -> str | None:
        live_key = os.getenv("BINANCE_LIVE_TRADE_API_KEY", "")
        live_secret = os.getenv("BINANCE_LIVE_TRADE_API_SECRET", "")
        read_key = os.getenv("BINANCE_API_KEY", "")
        if not live_key or not live_secret:
            return "Missing BINANCE_LIVE_TRADE_API_KEY or BINANCE_LIVE_TRADE_API_SECRET."
        if live_key == read_key:
            return "Live trading key must not reuse the read-only key."
        return None

    def _validate_market_buy(self, symbol: str, quote_amount: Decimal, rules: SymbolRules, available_usdt: Decimal) -> str:
        allowed = {str(item).upper() for item in self.config.get("strategy", {}).get("allowed_symbols", [])}
        if symbol.upper() not in allowed:
            return f"{symbol} is not in strategy.allowed_symbols."
        if rules.status != "TRADING":
            return f"{symbol} status is {rules.status}, not TRADING."
        if rules.quote_asset != "USDT":
            return f"{symbol} quote asset is {rules.quote_asset}, expected USDT."
        if not rules.quote_order_qty_market_allowed:
            return f"{symbol} does not allow MARKET quoteOrderQty."
        if rules.min_notional and quote_amount < rules.min_notional:
            return f"Quote amount {quote_amount} USDT is below {symbol} minNotional {rules.min_notional}."
        if quote_amount > available_usdt:
            return f"Quote amount {quote_amount} USDT exceeds live spot free USDT balance {available_usdt}."
        return f"OK: {symbol} live preview passed filters and balance check."
