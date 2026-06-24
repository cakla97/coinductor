from __future__ import annotations

from .models import ActiveStrategiesReport, CapitalSourcingPlan, GridRecommendation, NextRunRecommendation, RebalancingBotRecommendation, RecommendedAction, RiskDecision, StrategyDecision


class RecommendedActionsBuilder:
    def build(
        self,
        strategy_decision: StrategyDecision,
        risk_decision: RiskDecision,
        grid_recommendation: GridRecommendation,
        rebalancing_bot_recommendation: RebalancingBotRecommendation,
        spot_capital_plan: CapitalSourcingPlan,
        grid_capital_plan: CapitalSourcingPlan,
        next_run: NextRunRecommendation,
        active_strategies: ActiveStrategiesReport,
    ) -> tuple[RecommendedAction, ...]:
        actions: list[RecommendedAction] = []

        funding = rebalancing_bot_recommendation.funding_plan
        if funding is not None and funding.missing_usdt > 0:
            actions.append(
                RecommendedAction(
                    priority="HIGH" if not rebalancing_bot_recommendation.deployment_allowed else "MEDIUM",
                    action="Review the Rebalancing Bot USDC funding plan.",
                    reason=funding.summary,
                )
            )

        if rebalancing_bot_recommendation.recommended:
            basket = ", ".join(
                f"{item.asset} {item.target_weight_pct}%"
                for item in rebalancing_bot_recommendation.assets
            )
            actions.append(
                RecommendedAction(
                    priority="MEDIUM",
                    action="Review manual Binance Rebalancing Bot setup.",
                    reason=(
                        f"Deterministic advisor allows a {rebalancing_bot_recommendation.mode.lower()} setup "
                        f"with {basket}, threshold {rebalancing_bot_recommendation.threshold_pct}%, and "
                        f"maximum investment {rebalancing_bot_recommendation.investment_usdt} USDC-equivalent."
                    ),
                )
            )

        for grid in active_strategies.grid_bots:
            if grid.state in {
                "STOP_LOSS_BREACH",
                "TAKE_PROFIT_REACHED",
                "RUNTIME_EXPIRED",
                "BELOW_RANGE",
                "ABOVE_RANGE",
                "NEAR_LOWER",
                "NEAR_UPPER",
                "UNKNOWN_PRICE",
            }:
                high_states = {"STOP_LOSS_BREACH", "TAKE_PROFIT_REACHED", "RUNTIME_EXPIRED", "BELOW_RANGE", "ABOVE_RANGE"}
                actions.append(
                    RecommendedAction(
                        priority="HIGH" if grid.state in high_states else "MEDIUM",
                        action=f"Review active grid bot {grid.bot.name or grid.bot.symbol}.",
                        reason=grid.recommendation,
                    )
                )

        if strategy_decision.decision_type == "GRID_BOT_RECOMMENDATION" and grid_recommendation.recommended:
            actions.append(
                RecommendedAction(
                    priority="HIGH",
                    action=f"Review manual Spot Grid setup for {grid_recommendation.symbol}.",
                    reason="Current market profile looks suitable for a range strategy, but bot creation is recommend-only.",
                )
            )
        elif grid_recommendation.symbol and grid_recommendation.market_status in {"SUITABLE", "WATCH"}:
            actions.append(
                RecommendedAction(
                    priority="MEDIUM" if grid_recommendation.market_status == "SUITABLE" else "LOW",
                    action=f"Monitor grid conditions for {grid_recommendation.symbol}; do not create it yet.",
                    reason=grid_recommendation.reason,
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
                    action=f"For the {label}, consider sourcing {plan.missing_usdt} {plan.quote_asset} manually; first candidate is {first.asset}.",
                    reason=plan.summary,
                )
            )
        else:
            actions.append(
                RecommendedAction(
                    priority="HIGH",
                    action=f"Do not execute the {label} until the {plan.missing_usdt} {plan.quote_asset} funding gap is resolved.",
                    reason=plan.summary,
                )
            )
