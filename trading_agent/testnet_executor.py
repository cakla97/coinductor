from __future__ import annotations

from decimal import Decimal
import json

from .binance_client import BinanceApiError, BinanceClient
from .decimal_utils import display, floor_to_step
from .messages import Message, render_message
from .models import OrderValidation, RiskDecision, SymbolRules, TestnetExecutedOrder, TestnetExecutionReport, TestnetOrderRequest, TestnetOrderResult, TradeProposal
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

    def market_sell_quantity(self, symbol: str, quantity: Decimal, client_order_id: str) -> TestnetOrderRequest:
        return TestnetOrderRequest(
            symbol=symbol.upper(),
            side="SELL",
            order_type="MARKET",
            quote_order_qty=None,
            quantity=quantity,
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

        intent_id = OrderIntentFactory(self.config).spot_intent_id(proposal, risk_decision)
        if intent_id in existing_intents:
            return TestnetExecutionReport(enabled=True, orders=(), summary=f"Skipped duplicate testnet order intent {intent_id}.")

        rules = self.client.get_symbol_rules(proposal.symbol)
        validation = self.validate_market_buy(proposal.symbol, risk_decision.adjusted_quote_amount_usdt, rules)
        if not validation.approved:
            order = TestnetExecutedOrder(
                intent_id=intent_id,
                symbol=proposal.symbol,
                side=proposal.action,
                quote_amount_usdt=validation.adjusted_quote_amount_usdt,
                client_order_id=f"bta-{intent_id}",
                submitted=False,
                status="REJECTED_BY_FILTERS",
                executed_quantity=Decimal("0"),
                cumulative_quote_qty=Decimal("0"),
                order_id="",
                queried_status="",
                validation_summary=validation.reason,
                message="Order was rejected locally before reaching Binance Spot Testnet.",
            )
            return TestnetExecutionReport(enabled=True, orders=(order,), summary=f"Rejected Spot Testnet {proposal.action} order for {proposal.symbol}: {validation.reason}")

        request = self.market_buy_quote(
            symbol=proposal.symbol,
            quote_amount_usdt=validation.adjusted_quote_amount_usdt,
            client_order_id=f"bta-{intent_id}",
        )
        result = self.submit(request, confirm)
        order = self._executed_order_from_result(intent_id, request, result, validation.reason)
        action = "Submitted" if result.submitted else "Prepared"
        return TestnetExecutionReport(
            enabled=True,
            orders=(order,),
            summary=f"{action} Spot Testnet {proposal.action} order for {proposal.symbol}: {result.status}.",
        )

    def validate_market_buy(self, symbol: str, quote_amount_usdt: Decimal, rules: SymbolRules | None = None, require_whitelist: bool = True) -> OrderValidation:
        rules = rules or self.client.get_symbol_rules(symbol)
        if require_whitelist:
            allowed = {item.upper() for item in self.config.get("strategy", {}).get("allowed_symbols", [])}
            if rules.symbol.upper() not in allowed:
                return OrderValidation(False, f"{rules.symbol} is not in strategy.allowed_symbols.", Decimal("0"))
        if rules.status != "TRADING":
            return OrderValidation(False, f"{rules.symbol} status is {rules.status}, not TRADING.", Decimal("0"))
        if rules.quote_asset != "USDT":
            return OrderValidation(False, f"{rules.symbol} quote asset is {rules.quote_asset}, expected USDT.", Decimal("0"))
        if not rules.quote_order_qty_market_allowed:
            return OrderValidation(False, f"{rules.symbol} does not allow MARKET quoteOrderQty.", Decimal("0"))

        max_quote = Decimal(str(self.config.get("testnet_execution", {}).get("max_quote_amount_usdt", "10")))
        adjusted = min(quote_amount_usdt, max_quote)
        if rules.min_notional and adjusted < rules.min_notional:
            # By far the most common way a small order is refused, and the one a
            # user can act on: raise the budget, or lower the tranche count. It
            # carries a message so the desktop is not left appending an English
            # sentence to a Czech one.
            reason = Message(
                "order_below_min_notional",
                {
                    "amount": display(adjusted),
                    "symbol": rules.symbol,
                    "minimum": display(rules.min_notional),
                },
            )
            return OrderValidation(False, render_message(reason), adjusted, reason_message=reason)
        return OrderValidation(
            True,
            f"{rules.symbol} filters passed: minNotional={rules.min_notional}, quoteOrderQtyMarketAllowed={rules.quote_order_qty_market_allowed}.",
            adjusted,
        )

    def validate_market_sell(self, symbol: str, quantity: Decimal, rules: SymbolRules | None = None) -> OrderValidation:
        rules = rules or self.client.get_symbol_rules(symbol)
        allowed = {item.upper() for item in self.config.get("strategy", {}).get("allowed_symbols", [])}
        if rules.symbol.upper() not in allowed:
            return OrderValidation(False, f"{rules.symbol} is not in strategy.allowed_symbols.", Decimal("0"))
        if rules.status != "TRADING":
            return OrderValidation(False, f"{rules.symbol} status is {rules.status}, not TRADING.", Decimal("0"))
        if rules.quote_asset != "USDT":
            return OrderValidation(False, f"{rules.symbol} quote asset is {rules.quote_asset}, expected USDT.", Decimal("0"))

        adjusted_quantity = self._floor_to_step(quantity, rules.step_size)
        if adjusted_quantity <= 0:
            return OrderValidation(False, f"Quantity {quantity} rounds to zero with stepSize {rules.step_size}.", Decimal("0"))
        if rules.min_qty and adjusted_quantity < rules.min_qty:
            return OrderValidation(False, f"Adjusted quantity {adjusted_quantity} is below {rules.symbol} minQty {rules.min_qty}.", adjusted_quantity)
        if rules.max_qty and adjusted_quantity > rules.max_qty:
            return OrderValidation(False, f"Adjusted quantity {adjusted_quantity} is above {rules.symbol} maxQty {rules.max_qty}.", adjusted_quantity)

        free_balance = self.client.testnet_free_balance(rules.base_asset)
        if adjusted_quantity > free_balance:
            return OrderValidation(False, f"Adjusted quantity {adjusted_quantity} exceeds free testnet {rules.base_asset} balance {free_balance}.", adjusted_quantity)

        estimated_notional = adjusted_quantity * self.client.get_symbol_price(rules.symbol)
        if rules.min_notional and estimated_notional < rules.min_notional:
            return OrderValidation(
                False,
                f"Estimated notional {estimated_notional:.8f} USDT is below {rules.symbol} minNotional {rules.min_notional}.",
                adjusted_quantity,
            )
        return OrderValidation(
            True,
            f"{rules.symbol} sell filters passed: quantity={adjusted_quantity}, estimatedNotional={estimated_notional:.8f}, freeBalance={free_balance}.",
            adjusted_quantity,
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
        validation_summary: str,
    ) -> TestnetExecutedOrder:
        response = json.loads(result.response) if result.response else {}
        order_id = str(response.get("orderId", ""))
        queried_status = ""
        if result.submitted and order_id:
            try:
                queried = self.client.query_order(request.symbol, order_id=order_id)
                queried_status = str(queried.get("status", ""))
            except BinanceApiError as exc:
                queried_status = f"QUERY_ERROR: {exc}"
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
            order_id=order_id,
            queried_status=queried_status,
            validation_summary=validation_summary,
            message=result.message,
        )

    def _floor_to_step(self, value: Decimal, step: Decimal) -> Decimal:
        return floor_to_step(value, step)
