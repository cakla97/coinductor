from __future__ import annotations

from .messages import Message, render_message, render_messages
from .models import NextRunRecommendation, StrategyDecision


class NextRunAdvisor:
    """When to look again, and why.

    Emits messages rather than sentences so the desktop can show this panel in
    the reader's language while the Markdown report stays English.
    """

    def recommend(self, decision: StrategyDecision) -> NextRunRecommendation:
        if decision.decision_type == "GRID_BOT_RECOMMENDATION":
            return self._build(
                hours=0,
                urgency="ACTION_REQUIRED",
                reason=Message("next_run_reason_grid"),
                triggers=(
                    Message("next_run_trigger_grid_created"),
                    Message("next_run_trigger_grid_range"),
                ),
            )

        if decision.decision_type == "SPOT_TRADE_RECOMMENDATION":
            return self._build(
                hours=24,
                urgency="NORMAL",
                reason=Message("next_run_reason_spot_trade"),
                triggers=(
                    Message("next_run_trigger_after_execution"),
                    Message("next_run_trigger_tp_sl"),
                ),
            )

        return self._build(
            hours=24,
            urgency="NORMAL",
            reason=Message("next_run_reason_no_action"),
            triggers=(
                Message("next_run_trigger_large_move"),
                Message("next_run_trigger_manual_change"),
            ),
        )

    def _build(
        self,
        hours: int,
        urgency: str,
        reason: Message,
        triggers: tuple[Message, ...],
    ) -> NextRunRecommendation:
        return NextRunRecommendation(
            run_again_in_hours=hours,
            urgency=urgency,
            reason=render_message(reason),
            triggers=render_messages(triggers),
            reason_message=reason,
            trigger_messages=triggers,
        )
