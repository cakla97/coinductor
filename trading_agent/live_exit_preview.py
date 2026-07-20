from __future__ import annotations

from decimal import Decimal

from .binance_client import BinanceApiError, BinanceClient
from .decimal_utils import floor_to_step
from .models import Balance, LiveExitPreviewItem, LiveExitPreviewReport, LivePositionSummary


class LiveExitPreviewBuilder:
    def __init__(self, config: dict):
        self.config = config
        self.client = BinanceClient(config)

    def build(self, live_positions: LivePositionSummary, balances: list[Balance]) -> LiveExitPreviewReport:
        if not live_positions.enabled:
            return LiveExitPreviewReport(enabled=False, items=(), summary="Live exit preview is disabled.")
        items = tuple(self._preview_position(position, balances) for position in live_positions.open_positions)
        ready = len([item for item in items if item.status == "READY"])
        blocked = len([item for item in items if item.status == "BLOCKED"])
        monitoring = len([item for item in items if item.status == "MONITORING"])
        summary = f"{ready} ready exit preview(s), {blocked} blocked exit preview(s), {monitoring} monitored open position(s)."
        return LiveExitPreviewReport(enabled=True, items=items, summary=summary)

    def _preview_position(self, position, balances: list[Balance]) -> LiveExitPreviewItem:
        if position.exit_preview_status not in {"STOP_LOSS_REVIEW", "TAKE_PROFIT_REVIEW"}:
            return self._item(
                position=position,
                status="MONITORING",
                reason=position.exit_preview_reason,
                adjusted_quantity=Decimal("0"),
                available_base=self._base_available(position.symbol, balances),
                estimated_quote=Decimal("0"),
            )

        try:
            rules = self.client.get_symbol_rules(position.symbol)
        except BinanceApiError as exc:
            return self._item(
                position=position,
                status="BLOCKED",
                reason=f"Could not load symbol rules: {exc}",
                adjusted_quantity=Decimal("0"),
                available_base=self._base_available(position.symbol, balances),
                estimated_quote=Decimal("0"),
            )

        available_base = self._balance_for_asset(rules.base_asset, balances)
        sellable_quantity = min(position.quantity, available_base)
        adjusted_quantity = self._round_step(sellable_quantity, rules.step_size)
        estimated_quote = adjusted_quantity * (position.current_price or Decimal("0"))
        if rules.status != "TRADING":
            status = "BLOCKED"
            reason = f"{position.symbol} status is {rules.status}, not TRADING."
        elif adjusted_quantity <= 0:
            status = "BLOCKED"
            reason = f"No sellable {rules.base_asset} quantity is available in Spot."
        elif adjusted_quantity < rules.min_qty:
            status = "BLOCKED"
            reason = f"Adjusted quantity {adjusted_quantity} is below minQty {rules.min_qty}."
        elif rules.min_notional and estimated_quote < rules.min_notional:
            status = "BLOCKED"
            reason = f"Estimated notional {estimated_quote} {rules.quote_asset} is below minNotional {rules.min_notional}."
        else:
            status = "READY"
            reason = f"{position.exit_preview_status}: {position.exit_preview_reason}"

        return self._item(
            position=position,
            status=status,
            reason=reason,
            adjusted_quantity=adjusted_quantity,
            available_base=available_base,
            estimated_quote=estimated_quote,
        )

    def _item(
        self,
        position,
        status: str,
        reason: str,
        adjusted_quantity: Decimal,
        available_base: Decimal,
        estimated_quote: Decimal,
    ) -> LiveExitPreviewItem:
        return LiveExitPreviewItem(
            intent_id=f"sell-{position.intent_id}",
            symbol=position.symbol,
            side="SELL",
            status=status,
            reason=reason,
            quantity=position.quantity,
            adjusted_quantity=adjusted_quantity,
            available_base=available_base,
            estimated_quote=estimated_quote,
            exit_trigger=position.exit_preview_status,
            confirmation_required="CONFIRM_MAINNET_SELL",
        )

    def _base_available(self, symbol: str, balances: list[Balance]) -> Decimal:
        for quote in ("USDC", "USDT", "FDUSD", "BTC", "ETH", "BNB"):
            if symbol.upper().endswith(quote):
                return self._balance_for_asset(symbol[: -len(quote)], balances)
        return Decimal("0")

    def _balance_for_asset(self, asset: str, balances: list[Balance]) -> Decimal:
        wanted = asset.upper()
        for balance in balances:
            if balance.asset.upper() == wanted:
                return balance.spot_free
        return Decimal("0")

    def _round_step(self, quantity: Decimal, step_size: Decimal) -> Decimal:
        return floor_to_step(quantity, step_size)
