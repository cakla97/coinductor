from __future__ import annotations

import os
from decimal import Decimal, ROUND_CEILING

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
        quote_asset = str(live_config.get("quote_asset", "USDT")).upper()
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
                        quote_asset=quote_asset,
                        status="BLOCKED",
                        validation_summary=key_check,
                        available_usdt=Decimal("0"),
                        missing_usdt=Decimal("0"),
                        funding_required=False,
                        funding_steps=(),
                        confirmation_required="CONFIRM_MAINNET_ORDER",
                    ),
                ),
                summary="LIVE_CONFIRM preview is blocked by key guard.",
            )

        try:
            rules = self.client.get_symbol_rules(proposal.symbol)
            available_quote = self.client.get_spot_free_balance(quote_asset)
            validation = self._validate_market_buy(proposal.symbol, quote_amount, rules, available_quote, quote_asset)
        except BinanceApiError as exc:
            return LivePreviewReport(
                enabled=True,
                orders=(
                    LiveOrderPreview(
                        symbol=proposal.symbol,
                        side=proposal.action,
                        order_type="MARKET",
                        quote_amount_usdt=quote_amount,
                        quote_asset=quote_asset,
                        status="BLOCKED",
                        validation_summary=str(exc),
                        available_usdt=Decimal("0"),
                        missing_usdt=Decimal("0"),
                        funding_required=False,
                        funding_steps=(),
                        confirmation_required="CONFIRM_MAINNET_ORDER",
                    ),
                ),
                summary="LIVE_CONFIRM preview is blocked by Binance API validation.",
            )

        status = "PREVIEW_READY" if validation.startswith("OK:") else "BLOCKED"
        missing_usdt = max(Decimal("0"), quote_amount - available_quote)
        funding_required = missing_usdt > 0
        return LivePreviewReport(
            enabled=True,
            orders=(
                LiveOrderPreview(
                    symbol=proposal.symbol,
                    side=proposal.action,
                    order_type="MARKET",
                    quote_amount_usdt=quote_amount,
                    quote_asset=quote_asset,
                    status=status,
                    validation_summary=validation,
                    available_usdt=available_quote,
                    missing_usdt=missing_usdt,
                    funding_required=funding_required,
                    funding_steps=self._funding_steps(quote_amount, available_quote, quote_asset) if funding_required else (),
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

    def _validate_market_buy(self, symbol: str, quote_amount: Decimal, rules: SymbolRules, available_quote: Decimal, quote_asset: str) -> str:
        allowed = {str(item).upper() for item in self.config.get("strategy", {}).get("allowed_symbols", [])}
        if symbol.upper() not in allowed:
            return f"{symbol} is not in strategy.allowed_symbols."
        if rules.status != "TRADING":
            return f"{symbol} status is {rules.status}, not TRADING."
        if rules.quote_asset != quote_asset:
            return f"{symbol} quote asset is {rules.quote_asset}, expected {quote_asset}."
        if not rules.quote_order_qty_market_allowed:
            return f"{symbol} does not allow MARKET quoteOrderQty."
        if rules.min_notional and quote_amount < rules.min_notional:
            return f"Quote amount {quote_amount} {quote_asset} is below {symbol} minNotional {rules.min_notional}."
        if quote_amount > available_quote:
            return f"Quote amount {quote_amount} {quote_asset} exceeds live spot free {quote_asset} balance {available_quote}."
        return f"OK: {symbol} live preview passed filters and balance check."

    def _funding_steps(self, quote_amount: Decimal, available_quote: Decimal, quote_asset: str) -> tuple[str, ...]:
        missing = max(Decimal("0"), quote_amount - available_quote)
        if missing <= 0:
            return ()
        buffer = Decimal(str(self.config.get("live_confirm", {}).get("funding_buffer_usdt", "1")))
        target = (missing + buffer).quantize(Decimal("0.01"), rounding=ROUND_CEILING)
        return (
            f"Manually redeem at least {target} {quote_asset} from Flexible Earn to Spot.",
            f"Wait until Binance shows the redeemed {quote_asset} as Spot free balance.",
            "Run `python -m trading_agent run --config config.example.toml --real-data --live-confirm-preview` again.",
            "Continue only if the LIVE_CONFIRM preview changes from BLOCKED to PREVIEW_READY.",
        )
