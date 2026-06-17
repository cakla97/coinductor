from __future__ import annotations

from .models import GridRecommendation, RiskDecision, StrategyDecision, TradeProposal


class StrategyDecisionEngine:
    def decide(
        self,
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        grid_recommendation: GridRecommendation,
    ) -> StrategyDecision:
        if grid_recommendation.recommended:
            return StrategyDecision(
                decision_type="GRID_BOT_RECOMMENDATION",
                priority="MEDIUM",
                summary="A Spot Grid setup looks suitable for current market conditions. Manual confirmation is required.",
                spot_trade=proposal if risk_decision.approved else None,
                grid=grid_recommendation,
                rebalancing_note="Keep rebalancing separate from grid capital until an active grid baseline is recorded.",
            )

        if risk_decision.approved:
            return StrategyDecision(
                decision_type="SPOT_TRADE_RECOMMENDATION",
                priority="LOW",
                summary="No grid setup is recommended, but the spot trade proposal passed MVP risk checks.",
                spot_trade=proposal,
                grid=grid_recommendation,
                rebalancing_note=None,
            )

        return StrategyDecision(
            decision_type="HOLD",
            priority="LOW",
            summary="No action is recommended. Risk or market filters rejected active strategies.",
            spot_trade=None,
            grid=grid_recommendation,
            rebalancing_note=None,
        )

