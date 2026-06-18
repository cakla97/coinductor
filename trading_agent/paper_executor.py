from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

from .models import MarketSnapshot, PaperExecutionReport, PaperOrder, RiskDecision, TradeProposal


class PaperExecutor:
    def __init__(self, config: dict):
        self.config = config

    def simulate_spot(self, proposal: TradeProposal, risk_decision: RiskDecision, snapshots: list[MarketSnapshot]) -> PaperExecutionReport:
        paper_config = self.config.get("paper", {})
        if not paper_config.get("enabled", False) or not paper_config.get("simulate_spot_trades", False):
            return PaperExecutionReport(enabled=False, orders=(), summary="Paper execution is disabled.")
        if not risk_decision.approved:
            return PaperExecutionReport(enabled=True, orders=(), summary="No paper order created because risk engine rejected the proposal.")
        if proposal.action != "BUY":
            return PaperExecutionReport(enabled=True, orders=(), summary=f"Paper simulation for {proposal.action} is not implemented yet.")

        snapshot = next((item for item in snapshots if item.symbol == proposal.symbol), None)
        if snapshot is None:
            return PaperExecutionReport(enabled=True, orders=(), summary=f"No market snapshot available for {proposal.symbol}.")

        fee_pct = Decimal(str(paper_config.get("fee_pct", 0))) / Decimal("100")
        slippage_pct = Decimal(str(paper_config.get("slippage_pct", 0))) / Decimal("100")
        quote_amount = risk_decision.adjusted_quote_amount_usdt
        simulated_price = snapshot.price * (Decimal("1") + slippage_pct)
        fee = quote_amount * fee_pct
        slippage = quote_amount * slippage_pct
        net_quote = quote_amount - fee
        quantity = (net_quote / simulated_price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
        stop_loss = simulated_price * (Decimal("1") - proposal.stop_loss_pct / Decimal("100"))
        take_profit = simulated_price * (Decimal("1") + proposal.take_profit_pct / Decimal("100"))
        order = PaperOrder(
            symbol=proposal.symbol,
            side=proposal.action,
            quote_amount_usdt=self._money(quote_amount),
            simulated_price=self._price(simulated_price),
            simulated_quantity=quantity,
            fee_usdt=self._money(fee),
            slippage_usdt=self._money(slippage),
            stop_loss_price=self._price(stop_loss),
            take_profit_price=self._price(take_profit),
            status="FILLED",
            reason="Paper fill created from approved spot proposal using current market snapshot.",
        )
        return PaperExecutionReport(
            enabled=True,
            orders=(order,),
            summary=f"Created 1 paper {proposal.action} order for {proposal.symbol}.",
        )

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _price(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)

