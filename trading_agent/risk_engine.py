from __future__ import annotations

from decimal import Decimal

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
            return RiskDecision(False, f"Symbol {proposal.symbol} is not whitelisted.", Decimal("0"))
        if proposal.action == "HOLD":
            return RiskDecision(False, "AI proposal is HOLD.", Decimal("0"))
        if proposal.action not in {"BUY", "SELL"}:
            return RiskDecision(False, f"Unsupported action {proposal.action}.", Decimal("0"))
        if proposal.confidence < Decimal(str(risk["min_ai_confidence"])):
            return RiskDecision(False, "Confidence is below configured minimum.", Decimal("0"))
        if risk_state.kill_switch_active:
            return RiskDecision(False, f"Live risk kill switch is active. {risk_state.summary}", Decimal("0"))
        if risk_state.cooldown_active:
            return RiskDecision(False, f"Loss cooldown is active. {risk_state.summary}", Decimal("0"))
        if risk_state.trades_today >= int(risk["max_trades_per_day"]):
            return RiskDecision(False, "Daily trade count limit reached.", Decimal("0"))
        if risk_state.daily_loss_pct >= Decimal(str(risk["max_daily_loss_pct"])):
            return RiskDecision(False, "Daily loss limit reached.", Decimal("0"))
        if risk_state.weekly_loss_pct >= Decimal(str(risk["max_weekly_loss_pct"])):
            return RiskDecision(False, "Weekly loss limit reached.", Decimal("0"))
        if not skip_consensus:
            consensus_reason = self._consensus_rejection(proposal, snapshots)
            if consensus_reason is not None:
                return RiskDecision(False, consensus_reason, Decimal("0"))
        if self.config["orders"]["require_stop_loss"] and proposal.stop_loss_pct <= 0:
            return RiskDecision(False, "Stop loss is required.", Decimal("0"))

        max_redeem = Decimal(str(self.config["earn"]["max_redeem_per_run_usdt"]))
        adjusted = min(proposal.quote_amount_usdt, max_redeem)
        reason = (
            "Proposal approved by live risk state and deterministic market consensus."
            if not skip_consensus
            else "Proposal approved by live risk state. Consensus/market-timing checks were intentionally "
            "skipped for this initial portfolio deployment tranche; all other deterministic limits still applied."
        )
        return RiskDecision(True, reason, adjusted)

    def _consensus_rejection(
        self,
        proposal: TradeProposal,
        snapshots: list[MarketSnapshot],
    ) -> str | None:
        consensus = self.config.get("consensus", {})
        if not consensus.get("enabled", True) or proposal.action != "BUY":
            return None
        snapshot = next((item for item in snapshots if item.symbol == proposal.symbol), None)
        if snapshot is None:
            return f"Consensus gate: no market snapshot is available for {proposal.symbol}."
        if consensus.get("require_risk_on", True) and snapshot.trend_regime != "RISK_ON":
            return f"Consensus gate: {proposal.symbol} trend regime is {snapshot.trend_regime}, not RISK_ON."
        if consensus.get("require_price_above_ema200", True) and snapshot.price <= snapshot.ema200:
            return f"Consensus gate: {proposal.symbol} price is not above EMA200."
        min_rsi = Decimal(str(consensus.get("min_rsi14", "45")))
        max_rsi = Decimal(str(consensus.get("max_rsi14", "68")))
        if not min_rsi <= snapshot.rsi14 <= max_rsi:
            return f"Consensus gate: {proposal.symbol} RSI14 {snapshot.rsi14} is outside {min_rsi}-{max_rsi}."
        if consensus.get("require_rising_volume", False) and snapshot.volume_trend != "rising":
            return f"Consensus gate: {proposal.symbol} volume trend is {snapshot.volume_trend}, not rising."
        return None
