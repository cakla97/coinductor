from __future__ import annotations

from .models import CapitalSourcingPlan, GridRecommendation, NextRunRecommendation, RecommendedAction, RiskDecision, StrategyDecision


class RecommendedActionsBuilder:
    def build(
        self,
        strategy_decision: StrategyDecision,
        risk_decision: RiskDecision,
        grid_recommendation: GridRecommendation,
        spot_capital_plan: CapitalSourcingPlan,
        grid_capital_plan: CapitalSourcingPlan,
        next_run: NextRunRecommendation,
    ) -> tuple[RecommendedAction, ...]:
        actions: list[RecommendedAction] = []

        if strategy_decision.decision_type == "GRID_BOT_RECOMMENDATION" and grid_recommendation.recommended:
            actions.append(
                RecommendedAction(
                    priority="HIGH",
                    action=f"Review manual Spot Grid setup for {grid_recommendation.symbol}.",
                    reason="Current market profile looks suitable for a range strategy, but bot creation is recommend-only.",
                )
            )
        elif risk_decision.approved:
            actions.append(
                RecommendedAction(
                    priority="MEDIUM",
                    action=f"Review spot trade proposal for {strategy_decision.spot_trade.symbol if strategy_decision.spot_trade else 'the selected symbol'}.",
                    reason="The proposal passed deterministic MVP risk checks, but execution is still manual/recommend-only.",
                )
            )
        else:
            actions.append(
                RecommendedAction(
                    priority="LOW",
                    action="Do not open a new trade from this run.",
                    reason=risk_decision.reason,
                )
            )

        self._append_capital_action(actions, "spot trade", spot_capital_plan)
        self._append_capital_action(actions, "grid setup", grid_capital_plan)

        actions.append(
            RecommendedAction(
                priority="MEDIUM" if next_run.urgency == "ACTION_REQUIRED" else "LOW",
                action=f"Run the assistant again in {next_run.run_again_in_hours} hours.",
                reason=next_run.reason,
            )
        )
        return tuple(actions)

    def _append_capital_action(self, actions: list[RecommendedAction], label: str, plan: CapitalSourcingPlan) -> None:
        if plan.missing_usdt <= 0:
            return
        if plan.recommended:
            first = plan.items[0]
            actions.append(
                RecommendedAction(
                    priority="MEDIUM",
                    action=f"For the {label}, consider sourcing {plan.missing_usdt} USDT manually; first candidate is {first.asset}.",
                    reason=plan.summary,
                )
            )
        else:
            actions.append(
                RecommendedAction(
                    priority="HIGH",
                    action=f"Do not execute the {label} until the {plan.missing_usdt} USDT funding gap is resolved.",
                    reason=plan.summary,
                )
            )

