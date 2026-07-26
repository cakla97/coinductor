from __future__ import annotations

import os
from decimal import Decimal, ROUND_CEILING

from .binance_client import BinanceApiError, BinanceClient
from .models import LiveOrderPreview, LivePreviewReport, RiskDecision, SymbolRules, TradeProposal, TradingBankrollReport
from .order_journal import OrderIntentFactory
from .runtime_flags import RuntimeFlags


class LivePreviewExecutor:
    def __init__(self, config: dict):
        self.config = config
        self.runtime = RuntimeFlags.from_config(config)
        self.client = BinanceClient(config, credential_profile="live_trade")

    def preview_spot_proposal(
        self,
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        bankroll: TradingBankrollReport | None = None,
        existing_intents: set[str] | None = None,
        require_whitelist: bool = True,
    ) -> LivePreviewReport:
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
        intent_id = OrderIntentFactory(self.config).spot_intent_id(proposal, risk_decision)
        if key_check is not None:
            return LivePreviewReport(
                enabled=True,
                orders=(
                    LiveOrderPreview(
                        intent_id=intent_id,
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
            validation = self._validate_market_buy(proposal.symbol, quote_amount, rules, available_quote, quote_asset, require_whitelist)
            bankroll_validation = self._validate_bankroll(bankroll)
            if bankroll_validation:
                validation = bankroll_validation
        except BinanceApiError as exc:
            return LivePreviewReport(
                enabled=True,
                orders=(
                    LiveOrderPreview(
                        intent_id=intent_id,
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
        if status == "PREVIEW_READY" and intent_id in (existing_intents or set()):
            status = "BLOCKED"
            validation = f"Live order intent {intent_id} was already submitted before."
        missing_usdt = max(Decimal("0"), quote_amount - available_quote)
        funding_required = missing_usdt > 0
        submitted = False
        order_id = ""
        executed_quantity = Decimal("0")
        cumulative_quote_qty = Decimal("0")
        message = "No mainnet order was submitted."
        if status == "PREVIEW_READY" and self._submit_requested():
            submit_result = self._submit_market_buy(proposal.symbol, quote_amount, intent_id)
            status = submit_result["status"]
            submitted = submit_result["submitted"]
            order_id = submit_result["order_id"]
            executed_quantity = submit_result["executed_quantity"]
            cumulative_quote_qty = submit_result["cumulative_quote_qty"]
            message = submit_result["message"]
        return LivePreviewReport(
            enabled=True,
            orders=(
                LiveOrderPreview(
                    intent_id=intent_id,
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
                    submitted=submitted,
                    order_id=order_id,
                    executed_quantity=executed_quantity,
                    cumulative_quote_qty=cumulative_quote_qty,
                    message=message,
                ),
            ),
            summary=f"LIVE_CONFIRM for {proposal.symbol}: {status}. {message}",
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

    def _validate_market_buy(self, symbol: str, quote_amount: Decimal, rules: SymbolRules, available_quote: Decimal, quote_asset: str, require_whitelist: bool = True) -> str:
        if require_whitelist:
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

    def _validate_bankroll(self, bankroll: TradingBankrollReport | None) -> str | None:
        if bankroll is None or not bankroll.enabled:
            return None
        allowed_sources = {
            "PROFIT_SPOT",
            "SEEDED_SPOT",
            "SPOT_AVAILABLE",
            "FLEXIBLE_EARN_REDEEM_REQUIRED",
        }
        if bankroll.preferred_source in allowed_sources:
            if bankroll.preferred_source == "FLEXIBLE_EARN_REDEEM_REQUIRED":
                return (
                    f"Bankroll policy allows Flexible Earn funding, but {bankroll.flexible_draw_needed} "
                    f"{bankroll.quote_asset} must be redeemed to Spot before order submission."
                )
            return None
        return f"Bankroll policy blocked live order: {bankroll.summary}"

    def _submit_requested(self) -> bool:
        return self.runtime.live_submit

    def _submit_market_buy(self, symbol: str, quote_amount: Decimal, intent_id: str) -> dict[str, object]:
        if self.runtime.mainnet_confirm != "CONFIRM_MAINNET_ORDER":
            return {
                "submitted": False,
                "status": "SUBMIT_SKIPPED",
                "order_id": "",
                "executed_quantity": Decimal("0"),
                "cumulative_quote_qty": Decimal("0"),
                "message": "Submit requested but confirmation string did not match CONFIRM_MAINNET_ORDER.",
            }
        client_order_id = self._client_order_id(symbol, intent_id)
        try:
            response = self.client.submit_market_buy_quote(symbol, quote_amount, client_order_id)
        except BinanceApiError as exc:
            return {
                "submitted": False,
                "status": "SUBMIT_ERROR",
                "order_id": "",
                "executed_quantity": Decimal("0"),
                "cumulative_quote_qty": Decimal("0"),
                "message": str(exc),
            }
        return {
            "submitted": True,
            "status": str(response.get("status", "SUBMITTED")),
            "order_id": str(response.get("orderId", "")),
            "executed_quantity": Decimal(str(response.get("executedQty", "0"))),
            "cumulative_quote_qty": Decimal(str(response.get("cummulativeQuoteQty", "0"))),
            "message": f"Mainnet order submitted with clientOrderId {client_order_id}.",
        }

    def _client_order_id(self, symbol: str, intent_id: str) -> str:
        return f"BTAL{symbol.upper()[:6]}{intent_id}"[:36]
