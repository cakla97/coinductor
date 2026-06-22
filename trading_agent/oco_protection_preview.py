from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN

from .binance_client import BinanceApiError, BinanceClient
from .models import Balance, LivePositionSummary, OcoProtectionPreviewItem, OcoProtectionPreviewReport


class OcoProtectionPreviewBuilder:
    def __init__(self, config: dict):
        self.config = config
        self.client = BinanceClient(config)
        self.live_client = BinanceClient(config, credential_profile="live_trade")

    def build(
        self,
        live_positions: LivePositionSummary,
        balances: list[Balance],
        existing_intents: set[str] | None = None,
    ) -> OcoProtectionPreviewReport:
        if not self.config.get("orders", {}).get("use_oco_when_live", True):
            return OcoProtectionPreviewReport(enabled=False, items=(), summary="OCO protection preview is disabled.")
        items = tuple(self._preview_position(position, balances, existing_intents or set()) for position in live_positions.open_positions)
        ready = len([item for item in items if item.status == "READY"])
        blocked = len([item for item in items if item.status == "BLOCKED"])
        monitoring = len([item for item in items if item.status == "MONITORING"])
        protected = len([item for item in items if item.status == "PROTECTED"])
        submitted = len([item for item in items if item.submitted])
        submit_note = f"{submitted} OCO order list(s) submitted." if submitted else "Preview only; no OCO order is submitted."
        summary = f"{ready} ready OCO protection preview(s), {blocked} blocked preview(s), {monitoring} monitored position(s), {protected} already protected position(s). {submit_note}"
        return OcoProtectionPreviewReport(enabled=True, items=items, summary=summary)

    def _preview_position(self, position, balances: list[Balance], existing_intents: set[str]) -> OcoProtectionPreviewItem:
        if position.current_price is None:
            return self._item(position, "BLOCKED", "Current price is unavailable.", Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), position.take_profit_price, position.stop_loss_price)
        try:
            rules = self.client.get_symbol_rules(position.symbol)
        except BinanceApiError as exc:
            return self._item(position, "BLOCKED", f"Could not load symbol rules: {exc}", Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), position.take_profit_price, position.stop_loss_price)

        available_base = self._balance_for_asset(rules.base_asset, balances)
        adjusted_quantity = self._round_step(min(position.quantity, available_base), rules.step_size)
        take_profit = self._round_price(position.take_profit_price, rules.tick_size)
        stop_loss = self._round_price(position.stop_loss_price, rules.tick_size)
        estimated_take_profit_quote = adjusted_quantity * take_profit
        estimated_stop_quote = adjusted_quantity * stop_loss

        if f"oco-{position.intent_id}" in existing_intents:
            return self._item(
                position,
                "PROTECTED",
                f"OCO intent oco-{position.intent_id} was already submitted before.",
                adjusted_quantity,
                available_base,
                estimated_take_profit_quote,
                estimated_stop_quote,
                take_profit,
                stop_loss,
            )

        if rules.status != "TRADING":
            return self._item(position, "BLOCKED", f"{position.symbol} status is {rules.status}, not TRADING.", adjusted_quantity, available_base, estimated_take_profit_quote, estimated_stop_quote, take_profit, stop_loss)
        if adjusted_quantity <= 0:
            return self._item(position, "BLOCKED", f"No sellable {rules.base_asset} quantity is available in Spot.", adjusted_quantity, available_base, estimated_take_profit_quote, estimated_stop_quote, take_profit, stop_loss)
        if adjusted_quantity < rules.min_qty:
            return self._item(position, "BLOCKED", f"Adjusted quantity {adjusted_quantity} is below minQty {rules.min_qty}.", adjusted_quantity, available_base, estimated_take_profit_quote, estimated_stop_quote, take_profit, stop_loss)
        if rules.min_notional and min(estimated_take_profit_quote, estimated_stop_quote) < rules.min_notional:
            return self._item(
                position,
                "BLOCKED",
                f"Estimated OCO notional is below minNotional {rules.min_notional}.",
                adjusted_quantity,
                available_base,
                estimated_take_profit_quote,
                estimated_stop_quote,
                take_profit,
                stop_loss,
            )
        if not (stop_loss < position.current_price < take_profit):
            return self._item(
                position,
                "BLOCKED",
                "OCO price relationship is invalid; expected stop loss below current price and take profit above current price.",
                adjusted_quantity,
                available_base,
                estimated_take_profit_quote,
                estimated_stop_quote,
                take_profit,
                stop_loss,
            )
        item = self._item(
            position,
            "READY",
            "SELL OCO protection preview is valid. It has not been submitted.",
            adjusted_quantity,
            available_base,
            estimated_take_profit_quote,
            estimated_stop_quote,
            take_profit,
            stop_loss,
        )
        return self._maybe_submit(item, existing_intents)

    def _item(
        self,
        position,
        status: str,
        reason: str,
        adjusted_quantity: Decimal,
        available_base: Decimal,
        estimated_take_profit_quote: Decimal,
        estimated_stop_quote: Decimal,
        take_profit_price: Decimal,
        stop_loss_stop_price: Decimal,
    ) -> OcoProtectionPreviewItem:
        return OcoProtectionPreviewItem(
            intent_id=f"oco-{position.intent_id}",
            symbol=position.symbol,
            side="SELL",
            status=status,
            reason=reason,
            quantity=position.quantity,
            adjusted_quantity=adjusted_quantity,
            available_base=available_base,
            take_profit_price=take_profit_price,
            stop_loss_stop_price=stop_loss_stop_price,
            estimated_take_profit_quote=estimated_take_profit_quote,
            estimated_stop_quote=estimated_stop_quote,
            confirmation_required="CONFIRM_MAINNET_OCO",
        )

    def _maybe_submit(self, item: OcoProtectionPreviewItem, existing_intents: set[str]) -> OcoProtectionPreviewItem:
        if item.intent_id in existing_intents:
            return self._replace_item(item, status="BLOCKED", reason=f"OCO intent {item.intent_id} was already submitted before.")
        if not self.config.get("_runtime", {}).get("oco_protection_submit", False):
            return item
        if str(self.config.get("_runtime", {}).get("mainnet_oco_confirm", "")) != "CONFIRM_MAINNET_OCO":
            return self._replace_item(item, status="SUBMIT_SKIPPED", message="OCO submit requested but confirmation string did not match CONFIRM_MAINNET_OCO.")

        list_client_id = self._client_order_id("OCOL", item.symbol, item.intent_id)
        above_client_id = self._client_order_id("OCOT", item.symbol, item.intent_id)
        below_client_id = self._client_order_id("OCOS", item.symbol, item.intent_id)
        try:
            response = self.live_client.submit_sell_oco_protection(
                symbol=item.symbol,
                quantity=item.adjusted_quantity,
                take_profit_price=item.take_profit_price,
                stop_loss_stop_price=item.stop_loss_stop_price,
                list_client_order_id=list_client_id,
                above_client_order_id=above_client_id,
                below_client_order_id=below_client_id,
            )
        except BinanceApiError as exc:
            return self._replace_item(item, status="SUBMIT_ERROR", message=str(exc))
        return self._replace_item(
            item,
            status=str(response.get("listOrderStatus", response.get("listStatusType", "SUBMITTED"))),
            submitted=True,
            order_list_id=str(response.get("orderListId", "")),
            message=f"OCO protection submitted with listClientOrderId {list_client_id}.",
        )

    def _replace_item(self, item: OcoProtectionPreviewItem, **changes) -> OcoProtectionPreviewItem:
        data = item.__dict__ | changes
        return OcoProtectionPreviewItem(**data)

    def _client_order_id(self, prefix: str, symbol: str, intent_id: str) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"{prefix}{symbol.upper()[:6]}{intent_id[-8:]}{timestamp[-10:]}"[:36]

    def _balance_for_asset(self, asset: str, balances: list[Balance]) -> Decimal:
        wanted = asset.upper()
        for balance in balances:
            if balance.asset.upper() == wanted:
                return balance.spot_free
        return Decimal("0")

    def _round_step(self, quantity: Decimal, step_size: Decimal) -> Decimal:
        if step_size <= 0:
            return quantity
        return (quantity / step_size).to_integral_value(rounding=ROUND_DOWN) * step_size

    def _round_price(self, price: Decimal, tick_size: Decimal) -> Decimal:
        if tick_size <= 0:
            return price
        return (price / tick_size).to_integral_value(rounding=ROUND_DOWN) * tick_size
