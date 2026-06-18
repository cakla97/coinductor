from __future__ import annotations

from decimal import Decimal
import json

from .binance_client import BinanceApiError, BinanceClient
from .models import TestnetOrderRequest, TestnetOrderResult


class TestnetExecutor:
    def __init__(self, config: dict):
        self.config = config
        self.client = BinanceClient(config, use_testnet=True)

    def market_buy_quote(self, symbol: str, quote_amount_usdt: Decimal, client_order_id: str) -> TestnetOrderRequest:
        return TestnetOrderRequest(
            symbol=symbol.upper(),
            side="BUY",
            order_type="MARKET",
            quote_order_qty=quote_amount_usdt,
            quantity=None,
            price=None,
            time_in_force=None,
            client_order_id=client_order_id,
        )

    def submit(self, request: TestnetOrderRequest, confirm: str) -> TestnetOrderResult:
        if confirm != "CONFIRM_TESTNET_ORDER":
            return TestnetOrderResult(
                submitted=False,
                status="SKIPPED",
                message="Confirmation string did not match CONFIRM_TESTNET_ORDER.",
                response="",
            )
        params: dict[str, object] = {
            "symbol": request.symbol,
            "side": request.side,
            "type": request.order_type,
            "newClientOrderId": request.client_order_id,
        }
        if request.quote_order_qty is not None:
            params["quoteOrderQty"] = str(request.quote_order_qty)
        if request.quantity is not None:
            params["quantity"] = str(request.quantity)
        if request.price is not None:
            params["price"] = str(request.price)
        if request.time_in_force is not None:
            params["timeInForce"] = request.time_in_force
        try:
            response = self.client.signed_post("/api/v3/order", params)
        except BinanceApiError as exc:
            return TestnetOrderResult(
                submitted=True,
                status="ERROR",
                message=str(exc),
                response="",
            )
        return TestnetOrderResult(
            submitted=True,
            status=str(response.get("status", "UNKNOWN")),
            message="Testnet order submitted.",
            response=json.dumps(response, default=str),
        )

