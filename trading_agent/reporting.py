from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .decimal_utils import display
from .models import ActiveStrategiesReport, AiCommentary, AiDecisionMemory, Balance, CapitalSourcingPlan, DustConversionPlan, EarnRedeemPlan, ExecutionChecklistItem, GridRecommendation, LiquidityDecision, LiveExitPreviewReport, LivePositionSummary, LivePreviewReport, LiveRiskState, MarketResearchReport, MarketSnapshot, NextRunRecommendation, OcoProtectionPreviewReport, OcoStatusReport, PaperExecutionReport, PortfolioAnalysis, RebalancePlan, RebalancingBotRecommendation, RecommendedAction, ResearchBundle, ResearchStatus, RiskDecision, ShadowEvaluationReport, StrategyDecision, TestnetExecutionReport, TestnetPositionSummary, TradeProposal, TradingBankrollReport


class Reporter:
    def __init__(self, reports_dir: Path, keep_last: int = 30):
        self.reports_dir = reports_dir
        self.keep_last = keep_last
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def write_report(
        self,
        run_id: int,
        mode: str,
        balances: list[Balance],
        portfolio_analysis: PortfolioAnalysis,
        rebalance_plan: RebalancePlan,
        rebalancing_bot_recommendation: RebalancingBotRecommendation,
        snapshots: list[MarketSnapshot],
        market_research: MarketResearchReport,
        proposal: TradeProposal,
        risk_state: LiveRiskState,
        risk_decision: RiskDecision,
        trading_bankroll: TradingBankrollReport,
        earn_redeem_plan: EarnRedeemPlan,
        paper_execution: PaperExecutionReport,
        testnet_execution: TestnetExecutionReport,
        live_preview: LivePreviewReport,
        testnet_positions: TestnetPositionSummary,
        live_positions: LivePositionSummary,
        live_exit_preview: LiveExitPreviewReport,
        oco_protection_preview: OcoProtectionPreviewReport,
        oco_status: OcoStatusReport,
        liquidity_decision: LiquidityDecision,
        grid_liquidity_decision: LiquidityDecision,
        spot_capital_plan: CapitalSourcingPlan,
        grid_capital_plan: CapitalSourcingPlan,
        dust_plan: DustConversionPlan,
        strategy_decision: StrategyDecision,
        next_run: NextRunRecommendation,
        recommended_actions: tuple[RecommendedAction, ...],
        execution_checklist: tuple[ExecutionChecklistItem, ...],
        ai_commentary: AiCommentary,
        research: ResearchBundle,
        research_status: ResearchStatus,
        active_strategies: ActiveStrategiesReport,
        decision_memory: AiDecisionMemory,
        shadow_evaluation: ShadowEvaluationReport,
    ) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = self.reports_dir / f"{timestamp}_run-{run_id}.md"
        lines = [
            f"# Trading Agent Report #{run_id}",
            "",
            f"- Mode: `{mode}`",
            f"- Generated: `{timestamp}`",
            "",
            "## Recommended Actions",
            "",
        ]
        for index, action in enumerate(recommended_actions, start=1):
            lines.extend(
                [
                    f"{index}. **{action.priority}** - {action.action}",
                    f"   Reason: {action.reason}",
                ]
            )
        lines.extend(["", "## Execution Checklist", ""])
        for index, item in enumerate(execution_checklist, start=1):
            lines.extend(
                [
                    f"{index}. **{item.priority}** - {item.step}",
                    f"   Detail: {item.detail}",
                ]
            )
        lines.extend(
            [
                "",
                "## AI Commentary",
                "",
                f"- Enabled: `{ai_commentary.enabled}`",
                f"- Summary: {ai_commentary.summary}",
                f"- Rebalancing assessment: {ai_commentary.rebalancing_assessment or 'Not provided.'}",
                "",
            ]
        )
        if ai_commentary.risks:
            lines.extend(["### Risks", ""])
            for risk in ai_commentary.risks:
                lines.append(f"- {risk}")
            lines.append("")
        if ai_commentary.watchlist:
            lines.extend(["### Watchlist", ""])
            for item in ai_commentary.watchlist:
                lines.append(f"- {item}")
            lines.append("")
        lines.extend(
            [
                "## Research Notes",
                "",
                f"- Enabled: `{research.enabled}`",
                f"- Notes loaded: `{len(research.notes)}`",
                f"- Fresh: `{research_status.is_fresh}`",
                f"- Summary: {research_status.summary}",
                "",
            ]
        )
        if research_status.request is not None:
            lines.extend(
                [
                    "### Generated Research Request",
                    "",
                    f"- Path: `{research_status.request.path}`",
                    f"- Title: {research_status.request.title}",
                    "",
                    "Run this request with Binance AI Agent Skills, then save the result into `research/notes/`.",
                    "",
                ]
            )
        if research.notes:
            for note in research.notes:
                lines.extend(
                    [
                        f"### {note.title}",
                        "",
                        f"- Source: `{note.source}`",
                        "",
                        note.content,
                        "",
                    ]
                )
        lines.extend(
            [
                "## Trading Bankroll",
                "",
                f"- Enabled: `{trading_bankroll.enabled}`",
                f"- Quote asset: `{trading_bankroll.quote_asset}`",
                f"- Initial seed: `{trading_bankroll.initial_seed} {trading_bankroll.quote_asset}`",
                f"- Spot free: `{trading_bankroll.spot_free} {trading_bankroll.quote_asset}`",
                f"- Flexible Earn: `{trading_bankroll.flexible_amount} {trading_bankroll.quote_asset}`",
                f"- Total tracked quote: `{trading_bankroll.total_quote} {trading_bankroll.quote_asset}`",
                f"- Estimated realized PnL vs seed: `{trading_bankroll.realized_pnl} {trading_bankroll.quote_asset}`",
                f"- Profit available in Spot: `{trading_bankroll.max_profit_trade_amount} {trading_bankroll.quote_asset}`",
                f"- Required amount: `{trading_bankroll.required_amount} {trading_bankroll.quote_asset}`",
                f"- Preferred source: `{trading_bankroll.preferred_source}`",
                f"- Flexible draw needed: `{trading_bankroll.flexible_draw_needed} {trading_bankroll.quote_asset}`",
                f"- Summary: {trading_bankroll.summary}",
                "",
            ]
        )
        lines.extend(
            [
                "## Flexible Earn Redeem",
                "",
                f"- Enabled: `{earn_redeem_plan.enabled}`",
                f"- Asset: `{earn_redeem_plan.asset}`",
                f"- Amount: `{earn_redeem_plan.amount}`",
                f"- Status: `{earn_redeem_plan.status}`",
                f"- Product ID: `{earn_redeem_plan.product_id}`",
                f"- Redeem type: `{earn_redeem_plan.redeem_type}`",
                f"- Can redeem: `{earn_redeem_plan.can_redeem}`",
                f"- Submitted: `{earn_redeem_plan.submitted}`",
                f"- Confirmation required: `{earn_redeem_plan.confirmation_required}`",
                f"- Message: {earn_redeem_plan.message}",
                "",
            ]
        )
        lines.extend(
            [
                "## Paper Execution",
                "",
                f"- Enabled: `{paper_execution.enabled}`",
                f"- Summary: {paper_execution.summary}",
                "",
            ]
        )
        if paper_execution.orders:
            lines.extend(
                [
                    "| Intent | Symbol | Side | Quote USDT | Sim Price | Quantity | Fee USDT | Slippage USDT | Stop | Take Profit | Status |",
                    "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
                ]
            )
            for order in paper_execution.orders:
                lines.append(
                    "| "
                    f"{order.intent_id} | {order.symbol} | {order.side} | {order.quote_amount_usdt} | {order.simulated_price} | "
                    f"{order.simulated_quantity} | {order.fee_usdt} | {order.slippage_usdt} | "
                    f"{order.stop_loss_price} | {order.take_profit_price} | {order.status} |"
                )
            lines.append("")
        lines.extend(
            [
                "## Spot Testnet Execution",
                "",
                f"- Enabled: `{testnet_execution.enabled}`",
                f"- Summary: {testnet_execution.summary}",
                "",
            ]
        )
        if testnet_execution.orders:
            lines.extend(
                [
                    "| Intent | Symbol | Side | Quote USDT | Client Order ID | Submitted | Status | Queried Status | Executed Qty | Cumulative Quote | Order ID | Validation | Message |",
                    "| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |",
                ]
            )
            for order in testnet_execution.orders:
                lines.append(
                    "| "
                    f"{order.intent_id} | {order.symbol} | {order.side} | {order.quote_amount_usdt} | "
                    f"{order.client_order_id} | {order.submitted} | {order.status} | {order.queried_status} | {order.executed_quantity} | "
                    f"{order.cumulative_quote_qty} | {order.order_id} | {order.validation_summary} | {order.message} |"
                )
            lines.append("")
        lines.extend(
            [
                "## Mainnet LIVE_CONFIRM Preview",
                "",
                f"- Enabled: `{live_preview.enabled}`",
                f"- Summary: {live_preview.summary}",
                "",
            ]
        )
        if live_preview.orders:
            lines.extend(
                [
                    "| Intent | Symbol | Side | Type | Quote Amount | Quote Asset | Status | Submitted | Order ID | Available Quote | Missing Quote | Funding Required | Confirmation Required | Validation | Message |",
                    "| --- | --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |",
                ]
            )
            for order in live_preview.orders:
                lines.append(
                    "| "
                    f"{order.intent_id} | {order.symbol} | {order.side} | {order.order_type} | {order.quote_amount_usdt} | "
                    f"{order.quote_asset} | {order.status} | {order.submitted} | {order.order_id} | "
                    f"{order.available_usdt} | {order.missing_usdt} | {order.funding_required} | "
                    f"{order.confirmation_required} | {order.validation_summary} | {order.message} |"
                )
            lines.append("")
            funding_steps = [step for order in live_preview.orders for step in order.funding_steps]
            if funding_steps:
                lines.extend(["### Manual Funding Checklist", ""])
                for index, step in enumerate(funding_steps, start=1):
                    lines.append(f"{index}. {step}")
                lines.append("")
        lines.extend(
            [
                "## Mainnet Live Positions",
                "",
                f"- Enabled: `{live_positions.enabled}`",
                f"- Summary: {live_positions.summary}",
                f"- Realized PnL: `{live_positions.total_realized_pnl_quote}`",
                "",
            ]
        )
        if live_positions.open_positions:
            lines.extend(
                [
                    "### Open Live Positions",
                    "",
                    "| Intent | Symbol | Buy Order ID | Quantity | Buy Quote | Entry | Current | Current Value | PnL | PnL % | Stop | Take Profit | Exit Preview | Reason |",
                    "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
                ]
            )
            for position in live_positions.open_positions:
                lines.append(
                    "| "
                    f"{position.intent_id} | {position.symbol} | {position.buy_order_id} | {position.quantity} | "
                    f"{position.buy_quote} | {position.entry_price} | {position.current_price if position.current_price is not None else ''} | "
                    f"{position.current_value if position.current_value is not None else ''} | {position.pnl_quote if position.pnl_quote is not None else ''} | "
                    f"{position.pnl_pct if position.pnl_pct is not None else ''} | {position.stop_loss_price} | {position.take_profit_price} | "
                    f"{position.exit_preview_status} | {position.exit_preview_reason} |"
                )
            lines.append("")
        if live_positions.closed_positions:
            lines.extend(
                [
                    "### Closed Live Cycles",
                    "",
                    "| Intent | Symbol | Buy Order ID | Sell Order ID | Quantity | Buy Quote | Sell Quote | PnL | PnL % |",
                    "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
                ]
            )
            for position in live_positions.closed_positions:
                lines.append(
                    "| "
                    f"{position.intent_id} | {position.symbol} | {position.buy_order_id} | {position.sell_order_id or ''} | "
                    f"{position.quantity} | {position.buy_quote} | {position.sell_quote or ''} | "
                    f"{position.pnl_quote if position.pnl_quote is not None else ''} | {position.pnl_pct if position.pnl_pct is not None else ''} |"
                )
            lines.append("")
        lines.extend(
            [
                "## Mainnet LIVE_EXIT Preview",
                "",
                f"- Enabled: `{live_exit_preview.enabled}`",
                f"- Summary: {live_exit_preview.summary}",
                "",
            ]
        )
        if live_exit_preview.items:
            lines.extend(
                [
                    "| Intent | Symbol | Side | Status | Quantity | Adjusted Quantity | Available Base | Estimated Quote | Trigger | Confirmation Required | Reason |",
                    "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
                ]
            )
            for item in live_exit_preview.items:
                lines.append(
                    "| "
                    f"{item.intent_id} | {item.symbol} | {item.side} | {item.status} | {item.quantity} | "
                    f"{item.adjusted_quantity} | {item.available_base} | {item.estimated_quote} | "
                    f"{item.exit_trigger} | {item.confirmation_required} | {item.reason} |"
                )
            lines.append("")
        lines.extend(
            [
                "## Mainnet OCO Protection Preview",
                "",
                f"- Enabled: `{oco_protection_preview.enabled}`",
                f"- Summary: {oco_protection_preview.summary}",
                "",
            ]
        )
        if oco_protection_preview.items:
            lines.extend(
                [
                    "| Intent | Symbol | Side | Status | Submitted | Order List ID | Quantity | Adjusted Quantity | Available Base | Take Profit | Stop Loss Stop | Estimated TP Quote | Estimated Stop Quote | Confirmation Required | Reason | Message |",
                    "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
                ]
            )
            for item in oco_protection_preview.items:
                lines.append(
                    "| "
                    f"{item.intent_id} | {item.symbol} | {item.side} | {item.status} | {item.submitted} | {item.order_list_id} | {item.quantity} | "
                    f"{item.adjusted_quantity} | {item.available_base} | {item.take_profit_price} | "
                    f"{item.stop_loss_stop_price} | {item.estimated_take_profit_quote} | {item.estimated_stop_quote} | "
                    f"{item.confirmation_required} | {item.reason} | {item.message} |"
                )
            lines.append("")
        lines.extend(
            [
                "## Mainnet OCO Status Sync",
                "",
                f"- Enabled: `{oco_status.enabled}`",
                f"- Summary: {oco_status.summary}",
                "",
            ]
        )
        if oco_status.items:
            lines.extend(
                [
                    "| Intent | Symbol | Order List ID | List Order Status | List Status Type | Filled Order ID | Filled Quantity | Filled Quote | Reconciled | Message |",
                    "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |",
                ]
            )
            for item in oco_status.items:
                lines.append(
                    "| "
                    f"{item.intent_id} | {item.symbol} | {item.order_list_id} | {item.list_order_status} | "
                    f"{item.list_status_type} | {item.filled_order_id} | {item.filled_quantity} | "
                    f"{item.filled_quote} | {item.reconciled} | {item.message} |"
                )
            lines.append("")
        lines.extend(
            [
                "## Spot Testnet Positions",
                "",
                f"- Enabled: `{testnet_positions.enabled}`",
                f"- Summary: {testnet_positions.summary}",
                f"- Realized PnL: `{testnet_positions.total_realized_pnl_usdt} USDT`",
                "",
            ]
        )
        if testnet_positions.open_positions:
            lines.extend(
                [
                    "### Open Testnet Positions",
                    "",
                    "| Symbol | Buy Order ID | Quantity | Buy Quote USDT | Status |",
                    "| --- | --- | ---: | ---: | --- |",
                ]
            )
            for position in testnet_positions.open_positions:
                lines.append(
                    f"| {position.symbol} | {position.buy_order_id} | {position.quantity} | {position.buy_quote_usdt} | {position.status} |"
                )
            lines.append("")
        if testnet_positions.closed_positions:
            lines.extend(
                [
                    "### Closed Testnet Cycles",
                    "",
                    "| Symbol | Buy Order ID | Sell Order ID | Quantity | Buy Quote USDT | Sell Quote USDT | PnL USDT |",
                    "| --- | --- | --- | ---: | ---: | ---: | ---: |",
                ]
            )
            for position in testnet_positions.closed_positions:
                lines.append(
                    "| "
                    f"{position.symbol} | {position.buy_order_id} | {position.sell_order_id or ''} | {position.quantity} | "
                    f"{position.buy_quote_usdt} | {position.sell_quote_usdt or ''} | {position.pnl_usdt or ''} |"
                )
            lines.append("")
        lines.extend(
            [
                "## Rebalancing Preview",
                "",
                f"- Enabled: `{rebalance_plan.enabled}`",
                f"- Preview only: `{rebalance_plan.preview_only}`",
                f"- Summary: {rebalance_plan.summary}",
                "",
            ]
        )
        if rebalance_plan.steps:
            lines.extend(
                [
                    "| Asset | Symbol | Side | Value USDT | Status | Reason |",
                    "| --- | --- | --- | ---: | --- | --- |",
                ]
            )
            for step in rebalance_plan.steps:
                lines.append(
                    f"| {step.asset} | {step.symbol or ''} | {step.side} | {step.value_usdt} | {step.status} | {step.reason} |"
                )
            lines.append("")
        lines.extend(
            [
                "## Binance Rebalancing Bot Advisor",
                "",
                f"- Enabled: `{rebalancing_bot_recommendation.enabled}`",
                f"- Deployment allowed: `{rebalancing_bot_recommendation.deployment_allowed}`",
                f"- Mode: `{rebalancing_bot_recommendation.mode or 'N/A'}`",
                f"- Threshold: `{rebalancing_bot_recommendation.threshold_pct}%`",
                f"- Guarded investment: `{rebalancing_bot_recommendation.investment_usdt} USDC-equivalent`",
                f"- Summary: {rebalancing_bot_recommendation.summary}",
                "",
            ]
        )
        if rebalancing_bot_recommendation.assets:
            lines.extend(
                [
                    "| Asset | Role | Current Value | Portfolio Weight | Bot Target | Status | Reason |",
                    "| --- | --- | ---: | ---: | ---: | --- | --- |",
                ]
            )
            for item in rebalancing_bot_recommendation.assets:
                lines.append(
                    f"| {item.asset} | {item.role} | {item.current_value_usdt} | "
                    f"{item.current_weight_pct}% | {item.target_weight_pct}% | {item.status} | {item.reason} |"
                )
            lines.append("")
        funding = rebalancing_bot_recommendation.funding_plan
        if funding is not None:
            lines.extend(
                [
                    "### Funding Plan",
                    "",
                    f"- Required investment: `{funding.needed_usdt} {funding.quote_asset}`",
                    f"- Existing Spot + Flexible: `{funding.available_usdt} {funding.quote_asset}`",
                    f"- Initial funding gap: `{funding.missing_usdt} {funding.quote_asset}`",
                    f"- Summary: {funding.summary}",
                    "",
                ]
            )
            if funding.items:
                lines.extend(
                    [
                        "| Source Asset | Convert Value | Source % | Remaining Value | Remaining % | Reason |",
                        "| --- | ---: | ---: | ---: | ---: | --- |",
                    ]
                )
                for item in funding.items:
                    lines.append(
                        f"| {item.asset} | {item.value_usdt} | {item.source_pct_of_asset}% | "
                        f"{item.remaining_value_usdt} | {item.remaining_pct_of_asset}% | {item.reason} |"
                    )
                lines.append("")
        if rebalancing_bot_recommendation.blockers:
            lines.extend(["### Deployment Blockers", ""])
            lines.extend(f"- {item}" for item in rebalancing_bot_recommendation.blockers)
            lines.append("")
        if rebalancing_bot_recommendation.manual_steps:
            lines.extend(["### Manual Setup", ""])
            lines.extend(f"{index}. {item}" for index, item in enumerate(rebalancing_bot_recommendation.manual_steps, start=1))
            lines.append("")
        lines.extend(
            [
                "## Active Strategies",
                "",
                f"- Enabled: `{active_strategies.enabled}`",
                f"- Summary: {active_strategies.summary}",
                "",
            ]
        )
        if active_strategies.grid_bots:
            lines.extend(
                [
                    "| Name | Binance Bot ID | Symbol | Range | Stop / Take | Grids | Investment | Age | Current Price | State | Distance Lower | Distance Upper | Recommendation |",
                    "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |",
                ]
            )
            for item in active_strategies.grid_bots:
                lines.append(
                    "| "
                    f"{item.bot.name} | {item.bot.binance_bot_id} | {item.bot.symbol} | "
                    f"{item.bot.range_low}-{item.bot.range_high} | {item.bot.stop_loss_price}/{item.bot.take_profit_price} | "
                    f"{item.bot.grid_count} {item.bot.grid_type} | {item.bot.investment_usdt} | "
                    f"{item.age_days if item.age_days is not None else ''}d | "
                    f"{item.current_price if item.current_price is not None else ''} | {item.state} | "
                    f"{item.distance_to_lower_pct if item.distance_to_lower_pct is not None else ''}% | "
                    f"{item.distance_to_upper_pct if item.distance_to_upper_pct is not None else ''}% | "
                    f"{item.recommendation} |"
                )
            lines.append("")
        if active_strategies.rebalancing_bots:
            lines.extend(
                [
                    "### Active Rebalancing Bots",
                    "",
                    "| Name | Binance Bot ID | Assets | Target Weights | Current Theoretical Weights | Threshold | Investment | Age | State | Recommendation |",
                    "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
                ]
            )
            for item in active_strategies.rebalancing_bots:
                target = ", ".join(
                    f"{asset} {weight}%" for asset, weight in zip(item.bot.assets, item.bot.target_weights_pct)
                )
                current = ", ".join(
                    f"{asset} {weight}%"
                    for asset, weight in zip(item.bot.assets, item.current_weights_pct)
                ) or "Unavailable"
                lines.append(
                    "| "
                    f"{item.bot.name} | {item.bot.binance_bot_id} | {', '.join(item.bot.assets)} | "
                    f"{target} | {current} | {item.bot.threshold_pct}% | {item.bot.investment_usdt} | "
                    f"{item.age_days if item.age_days is not None else ''}d | {item.state} | {item.recommendation} |"
                )
            lines.append("")
        lines.extend(
            [
                "## Executive Summary",
                "",
                f"- Total portfolio value: `{portfolio_analysis.total_value_usdt} USDT`",
                f"- Liquid value: `{portfolio_analysis.liquid_value_usdt} USDT`",
                f"- Locked value: `{portfolio_analysis.locked_value_usdt} USDT` (`{portfolio_analysis.locked_pct}%`)",
                f"- Unpriced assets: `{', '.join(portfolio_analysis.unpriced_assets) if portfolio_analysis.unpriced_assets else 'None'}`",
                f"- Ignored internal assets: `{', '.join(portfolio_analysis.ignored_internal_assets) if portfolio_analysis.ignored_internal_assets else 'None'}`",
                f"- Rebalance: {portfolio_analysis.rebalance_summary}",
                f"- Liquidity: {portfolio_analysis.liquidity_summary}",
                "",
                "## Portfolio",
                "",
                "| Asset | Spot free | Flexible | Locked |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for balance in balances:
            lines.append(f"| {balance.asset} | {balance.spot_free} | {balance.flexible_amount} | {balance.locked_amount} |")
        lines.extend(
            [
                "",
                "## Portfolio Valuation",
                "",
                "| Asset | Role | Price USDT | Spot value | Flexible value | Locked value | Total value | Allocation | Target | Gap | Action |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for asset in portfolio_analysis.assets:
            target = "" if asset.target_pct is None else f"{asset.target_pct}%"
            gap = "" if asset.gap_pct is None else f"{asset.gap_pct:+}%"
            lines.append(
                "| "
                f"{asset.asset} | {asset.role} | {asset.price_usdt} | {asset.spot_value_usdt} | {asset.flexible_value_usdt} | "
                f"{asset.locked_value_usdt} | {asset.total_value_usdt} | {asset.allocation_pct}% | {target} | {gap} | "
                f"{asset.rebalance_action} |"
            )
        if portfolio_analysis.unpriced_assets:
            lines.extend(
                [
                    "",
                    "### Unpriced Assets",
                    "",
                    "These assets were present in balances but excluded from total value because no supported Binance price route was found.",
                    "",
                ]
            )
            for asset in portfolio_analysis.unpriced_assets:
                lines.append(f"- `{asset}`")
        if portfolio_analysis.ignored_internal_assets:
            lines.extend(
                [
                    "",
                    "### Ignored Internal Assets",
                    "",
                    "These tickers look like Binance internal voucher/accounting assets and are excluded from valuation to avoid double counting.",
                    "",
                ]
            )
            for asset in portfolio_analysis.ignored_internal_assets:
                lines.append(f"- `{asset}`")
        lines.extend(["", "## Market", "", "| Symbol | Price | RSI14 | EMA20 | EMA50 | EMA200 | Regime |", "| --- | ---: | ---: | ---: | ---: | ---: | --- |"])
        for snapshot in snapshots:
            lines.append(
                f"| {snapshot.symbol} | {snapshot.price:.2f} | {display(snapshot.rsi14)} | {snapshot.ema20:.2f} | {snapshot.ema50:.2f} | {snapshot.ema200:.2f} | {snapshot.trend_regime} |"
            )
        lines.extend(
            [
                "",
                "## Local Binance Market Research",
                "",
                f"- Enabled: `{market_research.enabled}`",
                f"- Status: `{market_research.status}`",
                f"- Summary: {market_research.summary}",
            ]
        )
        if market_research.errors:
            lines.extend(["", "### Research Warnings", ""])
            for error in market_research.errors:
                lines.append(f"- {error}")
        if market_research.symbols:
            lines.extend(
                [
                    "",
                    "### Allowed Symbol Context",
                    "",
                    "| Symbol | 24h | 7d | 30d | 30d Support | 30d Resistance | 24h Range | ATR % | vs EMA200 | vs BTC 24h | 24h Quote Volume | Trades |",
                    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
                ]
            )
            for item in market_research.symbols:
                lines.append(
                    f"| {item.symbol} | {item.change_24h_pct:.2f}% | {self._optional_pct(item.return_7d_pct)} | "
                    f"{self._optional_pct(item.return_30d_pct)} | {item.support_30d or 'n/a'} | "
                    f"{item.resistance_30d or 'n/a'} | {item.range_24h_pct:.2f}% | {item.atr_pct:.2f}% | "
                    f"{item.price_vs_ema200_pct:.2f}% | {self._optional_pct(item.relative_strength_vs_btc_24h_pct)} | "
                    f"{item.quote_volume_24h:.2f} | {item.trades_24h} |"
                )
        if market_research.breadth is not None:
            breadth = market_research.breadth
            lines.extend(
                [
                    "",
                    "### Market Breadth",
                    "",
                    f"- Quote universe: `{breadth.quote_asset}`",
                    f"- Liquid symbols analyzed: `{breadth.symbols_analyzed}`",
                    f"- Advancing / declining / unchanged: `{breadth.advancing} / {breadth.declining} / {breadth.unchanged}`",
                    f"- Advance ratio: `{breadth.advance_pct:.2f}%`",
                    f"- Median 24h change: `{breadth.median_change_24h_pct:.2f}%`",
                    "",
                    "| Group | Symbols |",
                    "| --- | --- |",
                    f"| Top gainers | {self._movers(breadth.top_gainers)} |",
                    f"| Top losers | {self._movers(breadth.top_losers)} |",
                    f"| Top volume | {self._movers(breadth.top_volume)} |",
                ]
            )
        lines.extend(
            [
                "",
                "## AI Proposal",
                "",
                f"- Action: `{proposal.action}`",
                f"- Symbol: `{proposal.symbol}`",
                f"- Confidence: `{proposal.confidence}`",
                f"- Quote amount: `{proposal.quote_amount_usdt} {self._quote_asset(proposal.symbol)}`",
                f"- Stop loss: `{proposal.stop_loss_pct}%`",
                f"- Take profit: `{proposal.take_profit_pct}%`",
                f"- Reason: {proposal.reason}",
                "",
                "### AI Decision Memory",
                "",
                f"- Enabled: `{decision_memory.enabled}`",
                f"- Summary: {decision_memory.summary}",
                f"- Closed cycles supplied: `{len(decision_memory.recent_cycles)}`",
                f"- Wins / losses: `{decision_memory.wins} / {decision_memory.losses}`",
                f"- Realized PnL in supplied cycles: `{decision_memory.total_realized_pnl_quote}` quote units",
                "",
                "### Qwen Shadow Evaluation",
                "",
                f"- Enabled: `{shadow_evaluation.enabled}`",
                f"- Summary: {shadow_evaluation.summary}",
                f"- Recording status: `{shadow_evaluation.recording_status}`",
                f"- Recording detail: {shadow_evaluation.recording_message}",
                f"- Pending / completed: `{shadow_evaluation.pending_count} / {shadow_evaluation.completed_count}`",
                f"- Correct / wrong / neutral: `{shadow_evaluation.correct_count} / {shadow_evaluation.wrong_count} / {shadow_evaluation.neutral_count}`",
            ]
        )
        if shadow_evaluation.current_signal is not None:
            signal = shadow_evaluation.current_signal
            lines.extend(
                [
                    "",
                    "#### Current Shadow Signal",
                    "",
                    f"- Run: `{signal.run_id}`",
                    f"- Action / symbol: `{signal.action} {signal.symbol}`",
                    f"- Entry price: `{signal.entry_price}`",
                    f"- Confidence: `{signal.confidence}`",
                    f"- Evaluation horizon: `{signal.horizon_hours} hours`",
                    f"- Status: `{signal.status}`",
                ]
            )
        if shadow_evaluation.newly_evaluated:
            lines.extend(
                [
                    "",
                    "#### Newly Evaluated Signals",
                    "",
                    "| Signal Run | Action | Symbol | Evaluated After | Symbol Return | Best Universe Result | Verdict | Score | Price Source |",
                    "| ---: | --- | --- | ---: | ---: | --- | --- | --- | --- |",
                ]
            )
            for item in shadow_evaluation.newly_evaluated:
                lines.append(
                    f"| {item.signal_run_id} | {item.action} | {item.symbol} | {item.elapsed_hours:.2f}h | "
                    f"{item.symbol_return_pct:+.2f}% | {item.best_universe_symbol} "
                    f"({item.best_universe_return_pct:+.2f}%) | {item.verdict} | {item.score} | {item.price_source} |"
                )
        lines.extend(
            [
                "",
                "## Live Risk State",
                "",
                f"- Summary: {risk_state.summary}",
                f"- Loss basis: `{risk_state.loss_basis_quote}` quote units",
                f"- Trades today: `{risk_state.trades_today}`",
                f"- Daily realized PnL: `{risk_state.daily_realized_pnl_quote}`",
                f"- Weekly realized PnL: `{risk_state.weekly_realized_pnl_quote}`",
                f"- Daily / weekly loss: `{risk_state.daily_loss_pct:.4f}% / {risk_state.weekly_loss_pct:.4f}%`",
                f"- Consecutive losses: `{risk_state.consecutive_losses}`",
                f"- Last loss at: `{risk_state.last_loss_at}`",
                f"- Hours since last loss: `{risk_state.hours_since_last_loss}`",
                f"- Cooldown active: `{risk_state.cooldown_active}`",
                f"- Daily / weekly limit reached: `{risk_state.daily_limit_reached} / {risk_state.weekly_limit_reached}`",
                f"- Consecutive-loss limit reached: `{risk_state.consecutive_loss_limit_reached}`",
                f"- Kill switch active: `{risk_state.kill_switch_active}`",
                "",
                "## Risk Decision",
                "",
                f"- Approved: `{risk_decision.approved}`",
                f"- Reason: {risk_decision.reason}",
                f"- Adjusted quote amount: `{risk_decision.adjusted_quote_amount_usdt} {self._quote_asset(proposal.symbol)}`",
                "",
                "## Liquidity Decision",
                "",
                f"- Approved: `{liquidity_decision.approved}`",
                f"- Reason: {liquidity_decision.reason}",
                f"- Redeem asset: `{liquidity_decision.redeem_asset}`",
                f"- Redeem amount: `{liquidity_decision.redeem_amount}`",
                "",
                "## Grid Liquidity Decision",
                "",
                f"- Approved: `{grid_liquidity_decision.approved}`",
                f"- Reason: {grid_liquidity_decision.reason}",
                f"- Redeem asset: `{grid_liquidity_decision.redeem_asset}`",
                f"- Redeem amount: `{grid_liquidity_decision.redeem_amount}`",
                "",
                "## Capital Sourcing",
                "",
                "### Spot Trade",
                "",
                *self._capital_plan_lines(spot_capital_plan),
                "",
                "### Grid Bot",
                "",
                *self._capital_plan_lines(grid_capital_plan),
                "",
                "## Dust / Airdrop Funding",
                "",
                f"- Enabled: `{dust_plan.enabled}`",
                f"- Quote asset: `{dust_plan.quote_asset}`",
                f"- Recommended: `{dust_plan.recommended}`",
                f"- Total value: `{dust_plan.total_value_usdt}`",
                f"- Summary: {dust_plan.summary}",
                "",
            ]
        )
        if dust_plan.items:
            lines.extend(["| Asset | Value | Action | Reason |", "| --- | ---: | --- | --- |"])
            for item in dust_plan.items:
                lines.append(f"| {item.asset} | {item.value_usdt} | {item.action} | {item.reason} |")
            lines.append("")
        lines.extend(
            [
                "## Strategy Decision",
                "",
                f"- Decision: `{strategy_decision.decision_type}`",
                f"- Priority: `{strategy_decision.priority}`",
                f"- Summary: {strategy_decision.summary}",
                f"- Rebalancing note: {strategy_decision.rebalancing_note or 'None'}",
                "",
            ]
        )
        if strategy_decision.grid is not None:
            grid = strategy_decision.grid
            lines.extend(
                [
                    "## Spot Grid Recommendation",
                    "",
                    f"- Recommended: `{grid.recommended}`",
                    f"- Market status: `{grid.market_status}`",
                    f"- Deployment allowed: `{grid.deployment_allowed}`",
                    f"- Symbol: `{grid.symbol}`",
                    f"- Reason: {grid.reason}",
                    f"- Suitability score: `{grid.score}/100`",
                    f"- Range low: `{grid.range_low}`",
                    f"- Range high: `{grid.range_high}`",
                    f"- Range width: `{grid.range_width_pct}%`",
                    f"- Grid count: `{grid.grid_count}`",
                    f"- Grid type: `{grid.grid_type}`",
                    f"- Estimated quote per grid: `{grid.estimated_quote_per_grid}`",
                    f"- Estimated grid spacing: `{grid.estimated_grid_spacing_pct}%`",
                    f"- Investment: `{self._grid_investment_text(grid)}`",
                    f"- Stop loss price: `{grid.stop_loss_price}`",
                    f"- Take profit price: `{grid.take_profit_price}`",
                    "",
                ]
            )
            if grid.blockers:
                lines.extend(["### Deployment Blockers", ""])
                for blocker in grid.blockers:
                    lines.append(f"- {blocker}")
                lines.append("")
            if grid.candidate_assessments:
                lines.extend(
                    [
                        "### Candidate Comparison",
                        "",
                        "| Symbol | Score | Market Status | Assessment |",
                        "| --- | ---: | --- | --- |",
                    ]
                )
                for candidate in grid.candidate_assessments:
                    lines.append(
                        f"| {candidate.symbol} | {candidate.score}/100 | "
                        f"{candidate.market_status} | {candidate.reason} |"
                    )
                lines.append("")
            if grid.manual_steps:
                lines.extend(["### Manual Setup Steps", ""])
                for index, step in enumerate(grid.manual_steps, start=1):
                    lines.append(f"{index}. {step}")
                lines.append("")
        lines.extend(
            [
                "## Next Run Recommendation",
                "",
                f"- Run again in: `{next_run.run_again_in_hours} hours`",
                f"- Urgency: `{next_run.urgency}`",
                f"- Reason: {next_run.reason}",
                "",
                "### Triggers",
                "",
            ]
        )
        for trigger in next_run.triggers:
            lines.append(f"- {trigger}")
        lines.extend(
            [
                "",
                "## Execution",
                "",
                "Mainnet live orders and Flexible Earn redeem are only submitted when explicitly requested and confirmed. Grid bot creation remains manual/preview-only.",
                "",
            ]
        )
        path.write_text("\n".join(lines), encoding="utf-8")
        self.cleanup_old_reports()
        return path

    def cleanup_old_reports(self) -> None:
        if self.keep_last <= 0:
            return
        reports = sorted(
            self.reports_dir.glob("*_run-*.md"),
            key=lambda report: report.stat().st_mtime,
            reverse=True,
        )
        for report in reports[self.keep_last :]:
            report.unlink()

    def _capital_plan_lines(self, plan: CapitalSourcingPlan) -> list[str]:
        lines = [
            f"- Needed: `{plan.needed_usdt} {plan.quote_asset}`",
            f"- Available {plan.quote_asset}: `{plan.available_usdt} {plan.quote_asset}`",
            f"- Missing: `{plan.missing_usdt} {plan.quote_asset}`",
            f"- Recommended: `{plan.recommended}`",
            f"- Summary: {plan.summary}",
        ]
        if plan.items:
            lines.extend(
                [
                    "",
                    "| Asset | Value | Use % of Asset | Remaining Value | Remaining % | Action | Reason |",
                    "| --- | ---: | ---: | ---: | ---: | --- | --- |",
                ]
            )
            for item in plan.items:
                lines.append(
                    "| "
                    f"{item.asset} | {item.value_usdt} | {item.source_pct_of_asset}% | "
                    f"{item.remaining_value_usdt} | {item.remaining_pct_of_asset}% | {item.action} | {item.reason} |"
                )
        return lines

    def _quote_asset(self, symbol: str) -> str:
        symbol = symbol.upper()
        for quote in ("USDC", "USDT", "FDUSD", "BTC", "ETH", "BNB"):
            if symbol.endswith(quote):
                return quote
        return "USDT"

    def _optional_pct(self, value) -> str:
        return f"{value:.2f}%" if value is not None else "n/a"

    def _movers(self, movers) -> str:
        if not movers:
            return "none"
        return ", ".join(f"{item.symbol} ({item.change_24h_pct:+.2f}%)" for item in movers)

    def _grid_investment_text(self, grid: GridRecommendation) -> str:
        if not grid.symbol:
            return "N/A"
        return f"{grid.investment_usdt} {self._quote_asset(grid.symbol)}"
