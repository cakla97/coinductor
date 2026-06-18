from __future__ import annotations

from decimal import Decimal
import json

from .binance_client import BinanceApiError, BinanceClient
from .models import RiskDecision, TestnetExecutedOrder, TestnetExecutionReport, TestnetOrderRequest, TestnetOrderResult, TradeProposal
from .order_journal import OrderIntentFactory


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

    def execute_spot_proposal(
        self,
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        existing_intents: set[str],
        confirm: str,
    ) -> TestnetExecutionReport:
        execution_config = self.config.get("testnet_execution", {})
        if not execution_config.get("enabled", False):
            return TestnetExecutionReport(enabled=False, orders=(), summary="Spot Testnet execution is disabled.")
        if not risk_decision.approved:
            return TestnetExecutionReport(enabled=True, orders=(), summary="No testnet order created because risk engine rejected the proposal.")
        if proposal.action != "BUY":
            return TestnetExecutionReport(enabled=True, orders=(), summary=f"Spot Testnet execution for {proposal.action} is not implemented yet.")

        quote_amount = risk_decision.adjusted_quote_amount_usdt
        max_quote = Decimal(str(execution_config.get("max_quote_amount_usdt", "10")))
        if quote_amount > max_quote:
            quote_amount = max_quote

        intent_id = OrderIntentFactory(self.config).spot_intent_id(proposal, risk_decision)
        if intent_id in existing_intents:
            return TestnetExecutionReport(enabled=True, orders=(), summary=f"Skipped duplicate testnet order intent {intent_id}.")

        request = self.market_buy_quote(
            symbol=proposal.symbol,
            quote_amount_usdt=quote_amount,
            client_order_id=f"bta-{intent_id}",
        )
        result = self.submit(request, confirm)
        order = self._executed_order_from_result(intent_id, request, result)
        action = "Submitted" if result.submitted else "Prepared"
        return TestnetExecutionReport(
            enabled=True,
            orders=(order,),
            summary=f"{action} Spot Testnet {proposal.action} order for {proposal.symbol}: {result.status}.",
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

    def _executed_order_from_result(
        self,
        intent_id: str,
        request: TestnetOrderRequest,
        result: TestnetOrderResult,
    ) -> TestnetExecutedOrder:
        response = json.loads(result.response) if result.response else {}
        return TestnetExecutedOrder(
            intent_id=intent_id,
            symbol=request.symbol,
            side=request.side,
            quote_amount_usdt=request.quote_order_qty or Decimal("0"),
            client_order_id=request.client_order_id,
            submitted=result.submitted,
            status=result.status,
            executed_quantity=Decimal(str(response.get("executedQty", "0"))),
            cumulative_quote_qty=Decimal(str(response.get("cummulativeQuoteQty", "0"))),
            order_id=str(response.get("orderId", "")),
            message=result.message,
        )
