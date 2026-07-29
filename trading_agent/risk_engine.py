from __future__ import annotations

from decimal import Decimal

from .decimal_utils import display
from .messages import Message, render_message
from .models import LiveRiskState, MarketSnapshot, RiskDecision, TradeProposal


class RiskEngine:
    def __init__(self, config: dict):
        self.config = config

    def evaluate(
        self,
        proposal: TradeProposal,
        risk_state: LiveRiskState,
        snapshots: list[MarketSnapshot],
        skip_consensus: bool = False,
        allowed_symbols: set[str] | None = None,
    ) -> RiskDecision:
        risk = self.config["risk"]
        # allowed_symbols lets a caller substitute a different, still-enforced
        # whitelist (e.g. a first-portfolio template's basket) instead of
        # strategy.allowed_symbols, which is specifically the tactical-trading
        # universe and may not include every basket asset. The symbol still has
        # to be in *some* explicit whitelist; this never disables the check.
        if allowed_symbols is None:
            allowed_symbols = set(self.config["strategy"]["allowed_symbols"])

        if proposal.symbol not in allowed_symbols:
            return self._reject(Message("risk_not_whitelisted", {"symbol": proposal.symbol}))
        if proposal.action == "HOLD":
            return self._reject(Message("risk_proposal_is_hold"))
        if proposal.action not in {"BUY", "SELL"}:
            return self._reject(Message("risk_unsupported_action", {"action": proposal.action}))
        if proposal.confidence < Decimal(str(risk["min_ai_confidence"])):
            return self._reject(Message("risk_confidence_too_low"))
        if risk_state.kill_switch_active:
            return self._reject(Message("risk_kill_switch", {"summary": risk_state.summary}))
        if risk_state.cooldown_active:
            return self._reject(Message("risk_cooldown", {"summary": risk_state.summary}))
        if risk_state.trades_today >= int(risk["max_trades_per_day"]):
            return self._reject(Message("risk_daily_trade_limit"))
        if risk_state.daily_loss_pct >= Decimal(str(risk["max_daily_loss_pct"])):
            return self._reject(Message("risk_daily_loss_limit"))
        if risk_state.weekly_loss_pct >= Decimal(str(risk["max_weekly_loss_pct"])):
            return self._reject(Message("risk_weekly_loss_limit"))
        if not skip_consensus:
            consensus_reason = self._consensus_rejection(proposal, snapshots)
            if consensus_reason is not None:
                return self._reject(consensus_reason)
        if self.config["orders"]["require_stop_loss"] and proposal.stop_loss_pct <= 0:
            return self._reject(Message("risk_stop_loss_required"))

        max_redeem = Decimal(str(self.config["earn"]["max_redeem_per_run_usdt"]))
        adjusted = min(proposal.quote_amount_usdt, max_redeem)
        approved = Message(
            "risk_approved" if not skip_consensus else "risk_approved_skip_consensus"
        )
        return RiskDecision(True, render_message(approved), adjusted, reason_message=approved)

    def _reject(self, message: Message) -> RiskDecision:
        """Render English once, here, so the string cannot drift from the key."""
        return RiskDecision(False, render_message(message), Decimal("0"), reason_message=message)

    def _consensus_rejection(
        self,
        proposal: TradeProposal,
        snapshots: list[MarketSnapshot],
    ) -> Message | None:
        consensus = self.config.get("consensus", {})
        if not consensus.get("enabled", True) or proposal.action != "BUY":
            return None
        snapshot = next((item for item in snapshots if item.symbol == proposal.symbol), None)
        if snapshot is None:
            return Message("risk_no_snapshot", {"symbol": proposal.symbol})
        if consensus.get("require_risk_on", True) and snapshot.trend_regime != "RISK_ON":
            return Message("risk_trend_not_risk_on", {"symbol": proposal.symbol, "regime": snapshot.trend_regime})
        if consensus.get("require_price_above_ema200", True) and snapshot.price <= snapshot.ema200:
            return Message("risk_below_ema200", {"symbol": proposal.symbol})
        min_rsi = Decimal(str(consensus.get("min_rsi14", "45")))
        max_rsi = Decimal(str(consensus.get("max_rsi14", "68")))
        if not min_rsi <= snapshot.rsi14 <= max_rsi:
            return Message(
                "risk_rsi_outside_band",
                {"symbol": proposal.symbol, "value": display(snapshot.rsi14),
                 "minimum": str(min_rsi), "maximum": str(max_rsi)},
            )
        if consensus.get("require_rising_volume", False) and snapshot.volume_trend != "rising":
            return Message("risk_volume_not_rising", {"symbol": proposal.symbol, "trend": snapshot.volume_trend})
        return None
