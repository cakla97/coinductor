from __future__ import annotations

from decimal import Decimal

from .models import RiskDecision, TradeProposal


class RiskEngine:
    def __init__(self, config: dict):
        self.config = config

    def evaluate(self, proposal: TradeProposal, trades_today: int, daily_loss_pct: Decimal, weekly_loss_pct: Decimal) -> RiskDecision:
        risk = self.config["risk"]
        allowed_symbols = set(self.config["strategy"]["allowed_symbols"])

        if proposal.symbol not in allowed_symbols:
            return RiskDecision(False, f"Symbol {proposal.symbol} is not whitelisted.", Decimal("0"))
        if proposal.action == "HOLD":
            return RiskDecision(False, "AI proposal is HOLD.", Decimal("0"))
        if proposal.action not in {"BUY", "SELL"}:
            return RiskDecision(False, f"Unsupported action {proposal.action}.", Decimal("0"))
        if proposal.confidence < Decimal(str(risk["min_ai_confidence"])):
            return RiskDecision(False, "Confidence is below configured minimum.", Decimal("0"))
        if trades_today >= int(risk["max_trades_per_day"]):
            return RiskDecision(False, "Daily trade count limit reached.", Decimal("0"))
        if daily_loss_pct >= Decimal(str(risk["max_daily_loss_pct"])):
            return RiskDecision(False, "Daily loss limit reached.", Decimal("0"))
        if weekly_loss_pct >= Decimal(str(risk["max_weekly_loss_pct"])):
            return RiskDecision(False, "Weekly loss limit reached.", Decimal("0"))
        if self.config["orders"]["require_stop_loss"] and proposal.stop_loss_pct <= 0:
            return RiskDecision(False, "Stop loss is required.", Decimal("0"))

        max_redeem = Decimal(str(self.config["earn"]["max_redeem_per_run_usdt"]))
        adjusted = min(proposal.quote_amount_usdt, max_redeem)
        return RiskDecision(True, "Proposal approved within MVP risk limits.", adjusted)

