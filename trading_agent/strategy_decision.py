from __future__ import annotations

from .messages import Message, render_message
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
                summary=render_message(Message("decision_summary_grid")),
                summary_message=Message("decision_summary_grid"),
                spot_trade=proposal if risk_decision.approved else None,
                grid=grid_recommendation,
                rebalancing_note="Keep rebalancing separate from grid capital until an active grid baseline is recorded.",
            )

        if risk_decision.approved:
            return StrategyDecision(
                decision_type="SPOT_TRADE_RECOMMENDATION",
                priority="LOW",
                summary=render_message(Message("decision_summary_spot_trade")),
                summary_message=Message("decision_summary_spot_trade"),
                spot_trade=proposal,
                grid=grid_recommendation,
                rebalancing_note=None,
            )

        return StrategyDecision(
            decision_type="HOLD",
            priority="LOW",
            summary=render_message(Message("decision_summary_hold")),
            summary_message=Message("decision_summary_hold"),
            spot_trade=None,
            grid=grid_recommendation,
            rebalancing_note=None,
        )

