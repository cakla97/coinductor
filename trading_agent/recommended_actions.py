from __future__ import annotations

from .messages import Message, render_message
from .models import ActiveStrategiesReport, CapitalSourcingPlan, GridRecommendation, NextRunRecommendation, RebalancingBotRecommendation, RecommendedAction, RiskDecision, StrategyDecision


class RecommendedActionsBuilder:
    """The short list at the top of the Overview.

    Each item is built from a message rather than a finished sentence, so the
    desktop can show it in the reader's language while the Markdown report
    stays English. The explanation under each headline is mostly borrowed from
    whichever advisor produced it, and travels as that advisor's own message
    where it has one; the few written here have their own keys.
    """

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
                self._action(
                    priority="HIGH" if not rebalancing_bot_recommendation.deployment_allowed else "MEDIUM",
                    action=Message("action_review_rebalance_funding"),
                    reason=funding.summary,
                    reason_message=funding.summary_step,
                )
            )

        if rebalancing_bot_recommendation.recommended:
            basket = ", ".join(
                f"{item.asset} {item.target_weight_pct}%"
                for item in rebalancing_bot_recommendation.assets
            )
            actions.append(
                self._action(
                    priority="MEDIUM",
                    action=Message("action_review_rebalance_setup"),
                    reason_message=Message(
                        "action_reason_rebalance_allowed",
                        {
                            "mode": rebalancing_bot_recommendation.mode.lower(),
                            "basket": basket,
                            "threshold": str(rebalancing_bot_recommendation.threshold_pct),
                            "investment": str(rebalancing_bot_recommendation.investment_usdt),
                        },
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
                    self._action(
                        priority="HIGH" if grid.state in high_states else "MEDIUM",
                        action=Message(
                            "action_review_active_grid",
                            {"name": grid.bot.name or grid.bot.symbol},
                        ),
                        # The active-strategy evaluator still writes prose.
                        reason=grid.recommendation,
                    )
                )

        if strategy_decision.decision_type == "GRID_BOT_RECOMMENDATION" and grid_recommendation.recommended:
            actions.append(
                self._action(
                    priority="HIGH",
                    action=Message(
                        "action_review_grid_setup",
                        {"symbol": grid_recommendation.symbol or ""},
                    ),
                    reason_message=Message("action_reason_grid_recommend_only"),
                )
            )
        elif grid_recommendation.symbol and grid_recommendation.market_status in {"SUITABLE", "WATCH"}:
            actions.append(
                self._action(
                    priority="MEDIUM" if grid_recommendation.market_status == "SUITABLE" else "LOW",
                    action=Message("action_monitor_grid", {"symbol": grid_recommendation.symbol}),
                    reason=grid_recommendation.reason,
                    reason_message=grid_recommendation.reason_message,
                    reason_parts=grid_recommendation.reason_part_messages,
                )
            )
        elif risk_decision.approved:
            actions.append(
                self._action(
                    priority="MEDIUM",
                    action=Message(
                        "action_review_spot_trade",
                        {
                            "symbol": strategy_decision.spot_trade.symbol
                            if strategy_decision.spot_trade
                            else "the selected symbol"
                        },
                    ),
                    reason_message=Message("action_reason_trade_passed_checks"),
                )
            )
        else:
            actions.append(
                self._action(
                    priority="LOW",
                    action=Message("action_no_new_trade"),
                    # The risk engine still writes prose.
                    reason=risk_decision.reason,
                )
            )

        self._append_capital_action(actions, "spot_trade", spot_capital_plan)
        self._append_capital_action(actions, "grid_setup", grid_capital_plan)

        actions.append(
            self._action(
                priority="MEDIUM" if next_run.urgency == "ACTION_REQUIRED" else "LOW",
                action=Message("action_run_again", {"hours": str(next_run.run_again_in_hours)}),
                reason=next_run.reason,
                reason_message=next_run.reason_message,
            )
        )
        return tuple(actions)

    def _action(
        self,
        priority: str,
        action: Message,
        reason: str = "",
        reason_message: Message | None = None,
        reason_parts: tuple[Message, ...] = (),
    ) -> RecommendedAction:
        """Render English once, here, so the strings cannot drift from the keys."""
        rendered_reason = reason
        if reason_message is not None and not rendered_reason:
            rendered_reason = render_message(reason_message)
        return RecommendedAction(
            priority=priority,
            action=render_message(action),
            reason=rendered_reason,
            action_message=action,
            reason_message=reason_message,
            reason_part_messages=reason_parts,
        )

    def _append_capital_action(
        self, actions: list[RecommendedAction], label: str, plan: CapitalSourcingPlan
    ) -> None:
        if plan.missing_usdt <= 0:
            return
        params = {"amount": str(plan.missing_usdt), "quote": plan.quote_asset}
        if plan.recommended:
            actions.append(
                self._action(
                    priority="MEDIUM",
                    action=Message(
                        f"action_source_capital_{label}",
                        {**params, "asset": plan.items[0].asset},
                    ),
                    reason=plan.summary,
                    reason_message=plan.summary_step,
                )
            )
        else:
            actions.append(
                self._action(
                    priority="HIGH",
                    action=Message(f"action_funding_gap_{label}", params),
                    reason=plan.summary,
                    reason_message=plan.summary_step,
                )
            )
