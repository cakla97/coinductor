from __future__ import annotations

from decimal import Decimal

from .binance_client import BinanceApiError, BinanceClient
from .models import OcoStatusItem, OcoStatusReport
from .storage import Storage


class OcoStatusSynchronizer:
    def __init__(self, config: dict, storage: Storage):
        self.config = config
        self.storage = storage
        self.client = BinanceClient(config, credential_profile="live_trade")

    def sync(self, run_id: int) -> OcoStatusReport:
        records = self.storage.get_submitted_oco_records()
        if not records:
            return OcoStatusReport(enabled=True, items=(), summary="No submitted OCO protection order lists are tracked.")
        items = tuple(self._sync_record(run_id, record) for record in records)
        reconciled = len([item for item in items if item.reconciled])
        active = len([item for item in items if item.list_order_status in {"EXECUTING", "NEW", "PARTIALLY_FILLED"}])
        closed = len([item for item in items if item.list_order_status in {"ALL_DONE", "DONE", "FILLED"}])
        errors = len([item for item in items if item.list_order_status == "QUERY_ERROR"])
        summary = f"{len(items)} OCO list(s) checked, {active} active, {closed} closed/done, {reconciled} reconciled sell(s), {errors} query error(s)."
        return OcoStatusReport(enabled=True, items=items, summary=summary)

    def _sync_record(self, run_id: int, record: dict[str, str]) -> OcoStatusItem:
        intent_id = record["intent_id"]
        symbol = record["symbol"]
        order_list_id = record["order_list_id"]
        try:
            order_list = self.client.query_order_list(order_list_id=order_list_id)
        except BinanceApiError as exc:
            return OcoStatusItem(intent_id, symbol, order_list_id, "QUERY_ERROR", "QUERY_ERROR", "", Decimal("0"), Decimal("0"), False, str(exc))

        list_order_status = str(order_list.get("listOrderStatus", ""))
        list_status_type = str(order_list.get("listStatusType", ""))
        filled_order = self._filled_sell_order(symbol, order_list)
        if filled_order is None:
            return OcoStatusItem(
                intent_id=intent_id,
                symbol=symbol,
                order_list_id=order_list_id,
                list_order_status=list_order_status,
                list_status_type=list_status_type,
                filled_order_id="",
                filled_quantity=Decimal("0"),
                filled_quote=Decimal("0"),
                reconciled=False,
                message="No filled SELL leg found yet.",
            )

        buy_intent = intent_id.removeprefix("oco-")
        sell_intent = f"sell-{buy_intent}"
        filled_quantity = Decimal(str(filled_order.get("executedQty", "0")))
        filled_quote = Decimal(str(filled_order.get("cummulativeQuoteQty", "0")))
        filled_order_id = str(filled_order.get("orderId", ""))
        if not self.storage.has_live_sell_for_intent(sell_intent):
            self.storage.record_live_sell_from_oco(
                run_id=run_id,
                intent_id=sell_intent,
                symbol=symbol,
                order_id=filled_order_id,
                executed_quantity=filled_quantity,
                cumulative_quote_qty=filled_quote,
                message=f"Reconciled from OCO orderListId {order_list_id}.",
            )
            reconciled = True
            message = "Filled SELL leg recorded into live_orders."
        else:
            reconciled = False
            message = "Filled SELL leg was already recorded before."
        return OcoStatusItem(
            intent_id=intent_id,
            symbol=symbol,
            order_list_id=order_list_id,
            list_order_status=list_order_status,
            list_status_type=list_status_type,
            filled_order_id=filled_order_id,
            filled_quantity=filled_quantity,
            filled_quote=filled_quote,
            reconciled=reconciled,
            message=message,
        )

    def _filled_sell_order(self, symbol: str, order_list: dict) -> dict | None:
        reports = list(order_list.get("orderReports", []))
        if not reports:
            for order in order_list.get("orders", []):
                order_id = str(order.get("orderId", ""))
                if order_id:
                    try:
                        reports.append(self.client.query_order(symbol, order_id=order_id))
                    except BinanceApiError:
                        continue
        for order in reports:
            if str(order.get("side", "")).upper() != "SELL":
                continue
            if str(order.get("status", "")).upper() != "FILLED":
                continue
            if Decimal(str(order.get("executedQty", "0"))) <= 0:
                continue
            return order
        return None
