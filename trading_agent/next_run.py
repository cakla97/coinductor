from __future__ import annotations

from .models import NextRunRecommendation, StrategyDecision


class NextRunAdvisor:
    def recommend(self, decision: StrategyDecision) -> NextRunRecommendation:
        if decision.decision_type == "GRID_BOT_RECOMMENDATION":
            return NextRunRecommendation(
                run_again_in_hours=0,
                urgency="ACTION_REQUIRED",
                reason="A manual Spot Grid setup was recommended. Run again after setup to record the active strategy baseline.",
                triggers=(
                    "Run immediately after creating or skipping the recommended grid bot.",
                    "Run sooner if price moves outside the proposed grid range.",
                ),
            )

        if decision.decision_type == "SPOT_TRADE_RECOMMENDATION":
            return NextRunRecommendation(
                run_again_in_hours=24,
                urgency="NORMAL",
                reason="A spot trade recommendation was produced. Recheck after the next daily market update.",
                triggers=(
                    "Run sooner after manual execution.",
                    "Run sooner if stop loss or take profit is hit.",
                ),
            )

        return NextRunRecommendation(
            run_again_in_hours=24,
            urgency="NORMAL",
            reason="No action was recommended. Daily review is enough unless the market changes sharply.",
            triggers=(
                "Run sooner after a large BTC or ETH move.",
                "Run sooner before making manual portfolio changes.",
            ),
        )
