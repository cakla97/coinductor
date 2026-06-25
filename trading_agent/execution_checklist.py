from __future__ import annotations

from .models import (
    CapitalSourcingPlan,
    EarnRedeemPlan,
    ExecutionChecklistItem,
    GridRecommendation,
    LiquidityDecision,
    LivePreviewReport,
    RebalancingBotRecommendation,
    ResearchStatus,
    RiskDecision,
    StrategyDecision,
    TradeProposal,
    TradingBankrollReport,
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
        rebalancing_bot_recommendation: RebalancingBotRecommendation,
        strategy_decision: StrategyDecision,
        research_status: ResearchStatus,
        trading_bankroll: TradingBankrollReport,
        earn_redeem_plan: EarnRedeemPlan,
        live_preview: LivePreviewReport,
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
                        step="Prepare full-size spot trade liquidity",
                        detail=self._spot_liquidity_detail(liquidity_decision, trading_bankroll),
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

        if rebalancing_bot_recommendation.recommended:
            allocation = ", ".join(
                f"{item.asset} {item.target_weight_pct}%"
                for item in rebalancing_bot_recommendation.assets
            )
            items.append(
                ExecutionChecklistItem(
                    priority="MANUAL",
                    step="Create Binance Rebalancing Bot manually",
                    detail=(
                        f"Start with Equal, manually edit to {allocation}; enable Auto Rebalance By Ratio at "
                        f"{rebalancing_bot_recommendation.threshold_pct}%; investment no more than "
                        f"{rebalancing_bot_recommendation.investment_usdt} USDC. Keep Trigger Price and Stop Trigger OFF, "
                        "Sell All Coins on Stop OFF, fund from separate USDC, and keep WBETH outside the bot."
                    ),
                )
            )
            items.append(
                ExecutionChecklistItem(
                    priority="MANUAL",
                    step="Register the created Rebalancing Bot locally",
                    detail=(
                        "Use `python -m trading_agent rebalancing-register` with the exact Binance bot ID, "
                        "weights, entry prices, investment, and threshold shown after creation."
                    ),
                )
            )
        elif rebalancing_bot_recommendation.funding_plan is not None:
            for source in rebalancing_bot_recommendation.funding_plan.items:
                items.append(
                    ExecutionChecklistItem(
                        priority="MANUAL",
                        step=f"Prepare {source.asset} funding for Rebalancing Bot",
                        detail=(
                            f"{source.action} Keep approximately {source.remaining_value_usdt} USDC-equivalent "
                            f"({source.remaining_pct_of_asset}%) in {source.asset}. {source.reason}"
                        ),
                    )
                )
            items.append(
                ExecutionChecklistItem(
                    priority="BLOCKER",
                    step="Resolve remaining Rebalancing Bot funding gap",
                    detail=rebalancing_bot_recommendation.funding_plan.summary,
                )
            )

        self._append_first_live_action_gate(items, trading_bankroll, earn_redeem_plan, live_preview)
        self._append_capital_steps(
            items,
            "full-size spot trade",
            spot_capital_plan,
            priority="OPTIONAL",
            detail_prefix="Not required for the first small LIVE test. ",
        )

        items.append(
            ExecutionChecklistItem(
                priority="INFO",
                step="No automatic execution was performed",
                detail="This run did not place orders, redeem Earn products, or create Binance trading bots.",
            )
        )
        return tuple(items)

    def _append_first_live_action_gate(
        self,
        items: list[ExecutionChecklistItem],
        bankroll: TradingBankrollReport,
        earn_redeem_plan: EarnRedeemPlan,
        live_preview: LivePreviewReport,
    ) -> None:
        items.append(
            ExecutionChecklistItem(
                priority="GATE",
                step="First LIVE action gate",
                detail=(
                    f"Required {bankroll.required_amount} {bankroll.quote_asset}; spot free "
                    f"{bankroll.spot_free} {bankroll.quote_asset}; preferred source "
                    f"{bankroll.preferred_source}; flexible draw needed {bankroll.flexible_draw_needed} "
                    f"{bankroll.quote_asset}."
                ),
            )
        )
        if bankroll.flexible_draw_needed > 0 and earn_redeem_plan.enabled and earn_redeem_plan.status != "NOT_NEEDED":
            priority = "MANUAL" if earn_redeem_plan.status == "PREVIEW_READY" else "BLOCKER"
            items.append(
                ExecutionChecklistItem(
                    priority=priority,
                    step="Resolve USDC Flexible Earn funding before live order",
                    detail=(
                        f"Earn redeem status is {earn_redeem_plan.status}; amount "
                        f"{earn_redeem_plan.amount} {earn_redeem_plan.asset or bankroll.quote_asset}; "
                        f"submitted={earn_redeem_plan.submitted}. {earn_redeem_plan.message}"
                    ),
                )
            )
        if not live_preview.enabled:
            items.append(
                ExecutionChecklistItem(
                    priority="BLOCKER",
                    step="Run LIVE_CONFIRM preview before submit",
                    detail="Use --live-confirm-preview and continue only after the preview report is enabled.",
                )
            )
            return
        if not live_preview.orders:
            items.append(
                ExecutionChecklistItem(
                    priority="BLOCKER",
                    step="Wait for an actionable live order preview",
                    detail=live_preview.summary,
                )
            )
            return
        for order in live_preview.orders:
            if order.status == "PREVIEW_READY":
                items.append(
                    ExecutionChecklistItem(
                        priority="CONFIRM",
                        step=f"Live submit is eligible for {order.side} {order.symbol}",
                        detail=(
                            f"Preview passed for {order.quote_amount_usdt} {order.quote_asset}. "
                            "Submit only with --live-confirm-submit --confirm-mainnet-order CONFIRM_MAINNET_ORDER."
                        ),
                    )
                )
            else:
                items.append(
                    ExecutionChecklistItem(
                        priority="BLOCKER",
                        step=f"Live submit blocked for {order.side} {order.symbol}",
                        detail=f"{order.validation_summary} {order.message}",
                    )
                )

    def _quote_asset(self, symbol: str) -> str:
        symbol = symbol.upper()
        for quote in ("USDC", "USDT", "FDUSD", "BTC", "ETH", "BNB"):
            if symbol.endswith(quote):
                return quote
        return "USDT"

    def _spot_liquidity_detail(self, liquidity: LiquidityDecision, bankroll: TradingBankrollReport) -> str:
        base = (
            f"Full-size strategy would need {liquidity.redeem_amount} {liquidity.redeem_asset} "
            "made available before placing the full spot trade."
        )
        if bankroll.flexible_draw_needed > 0 and bankroll.flexible_draw_needed < liquidity.redeem_amount:
            return (
                f"{base} The first small LIVE test currently needs only "
                f"{bankroll.flexible_draw_needed} {bankroll.quote_asset}; follow the First LIVE action gate below."
            )
        return base

    def _append_capital_steps(
        self,
        items: list[ExecutionChecklistItem],
        label: str,
        plan: CapitalSourcingPlan,
        priority: str = "MANUAL",
        detail_prefix: str = "",
    ) -> None:
        if plan.missing_usdt <= 0:
            return
        if not plan.recommended:
            items.append(
                ExecutionChecklistItem(
                    priority="BLOCKER" if priority != "OPTIONAL" else "OPTIONAL",
                    step=f"Resolve {label} funding gap",
                    detail=f"{detail_prefix}{plan.summary}",
                )
            )
            return
        for item in plan.items:
            items.append(
                ExecutionChecklistItem(
                    priority=priority,
                    step=f"Source capital for {label} from {item.asset}",
                    detail=f"{detail_prefix}{item.action} Reason: {item.reason}",
                )
            )
