from __future__ import annotations

from .models import (
    CapitalSourcingPlan,
    ExecutionChecklistItem,
    GridRecommendation,
    LiquidityDecision,
    ResearchStatus,
    RiskDecision,
    StrategyDecision,
    TradeProposal,
)


class ExecutionChecklistBuilder:
    def build(
        self,
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        liquidity_decision: LiquidityDecision,
        grid_liquidity_decision: LiquidityDecision,
        spot_capital_plan: CapitalSourcingPlan,
        grid_capital_plan: CapitalSourcingPlan,
        grid_recommendation: GridRecommendation,
        strategy_decision: StrategyDecision,
        research_status: ResearchStatus,
    ) -> tuple[ExecutionChecklistItem, ...]:
        items: list[ExecutionChecklistItem] = []

        if research_status.request is not None:
            items.append(
                ExecutionChecklistItem(
                    priority="OPTIONAL",
                    step="Run fresh Binance skills research",
                    detail=(
                        f"Open `{research_status.request.path}`, run it with Binance AI Agent Skills, "
                        "save the result into `research/notes/`, then rerun the assistant with `--ai-commentary`."
                    ),
                )
            )

        self._append_capital_steps(items, "spot trade", spot_capital_plan)

        if risk_decision.approved:
            quote_asset = self._quote_asset(proposal.symbol)
            items.append(
                ExecutionChecklistItem(
                    priority="MANUAL",
                    step=f"Review spot trade {proposal.action} {proposal.symbol}",
                    detail=(
                        f"Proposed amount is {risk_decision.adjusted_quote_amount_usdt} {quote_asset}. "
                        f"Use stop loss {proposal.stop_loss_pct}% and take profit {proposal.take_profit_pct}% if manually executing. "
                        "Do not execute if funding, risk, or market context has changed."
                    ),
                )
            )
            if liquidity_decision.redeem_amount > 0:
                items.append(
                    ExecutionChecklistItem(
                        priority="MANUAL",
                        step="Prepare spot trade liquidity",
                        detail=(
                            f"Redeem or otherwise make available {liquidity_decision.redeem_amount} "
                            f"{liquidity_decision.redeem_asset} before placing the spot trade."
                        ),
                    )
                )

        if strategy_decision.decision_type == "GRID_BOT_RECOMMENDATION" and grid_recommendation.recommended:
            self._append_capital_steps(items, "grid setup", grid_capital_plan)
            if grid_liquidity_decision.redeem_amount > 0:
                items.append(
                    ExecutionChecklistItem(
                        priority="MANUAL",
                        step="Prepare grid liquidity",
                        detail=(
                            f"Redeem or make available {grid_liquidity_decision.redeem_amount} "
                            f"{grid_liquidity_decision.redeem_asset} for the grid allocation."
                        ),
                    )
                )
            items.append(
                ExecutionChecklistItem(
                    priority="MANUAL",
                    step=f"Create Spot Grid manually for {grid_recommendation.symbol}",
                    detail=(
                        f"Range {grid_recommendation.range_low}-{grid_recommendation.range_high}, "
                        f"{grid_recommendation.grid_count} {grid_recommendation.grid_type} grids, "
                        f"investment {grid_recommendation.investment_usdt} {self._quote_asset(grid_recommendation.symbol or '')}, "
                        f"stop around {grid_recommendation.stop_loss_price}, take profit around {grid_recommendation.take_profit_price}."
                    ),
                )
            )
            items.append(
                ExecutionChecklistItem(
                    priority="MANUAL",
                    step="Record the active grid state",
                    detail=(
                        "Copy `state/active_strategies.example.toml` to `state/active_strategies.toml`, "
                        "enter the real grid parameters, then rerun the assistant."
                    ),
                )
            )

        items.append(
            ExecutionChecklistItem(
                priority="INFO",
                step="No automatic execution was performed",
                detail="This run did not place orders, redeem Earn products, or create grid bots.",
            )
        )
        return tuple(items)

    def _quote_asset(self, symbol: str) -> str:
        symbol = symbol.upper()
        for quote in ("USDC", "USDT", "FDUSD", "BTC", "ETH", "BNB"):
            if symbol.endswith(quote):
                return quote
        return "USDT"

    def _append_capital_steps(self, items: list[ExecutionChecklistItem], label: str, plan: CapitalSourcingPlan) -> None:
        if plan.missing_usdt <= 0:
            return
        if not plan.recommended:
            items.append(
                ExecutionChecklistItem(
                    priority="BLOCKER",
                    step=f"Resolve {label} funding gap",
                    detail=plan.summary,
                )
            )
            return
        for item in plan.items:
            items.append(
                ExecutionChecklistItem(
                    priority="MANUAL",
                    step=f"Source capital for {label} from {item.asset}",
                    detail=f"{item.action} Reason: {item.reason}",
                )
            )
