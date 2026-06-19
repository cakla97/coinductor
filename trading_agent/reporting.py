from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import ActiveStrategiesReport, AiCommentary, Balance, CapitalSourcingPlan, ExecutionChecklistItem, LiquidityDecision, LivePreviewReport, MarketSnapshot, NextRunRecommendation, PaperExecutionReport, PortfolioAnalysis, RebalancePlan, RecommendedAction, ResearchBundle, ResearchStatus, RiskDecision, StrategyDecision, TestnetExecutionReport, TestnetPositionSummary, TradeProposal


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
        snapshots: list[MarketSnapshot],
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        paper_execution: PaperExecutionReport,
        testnet_execution: TestnetExecutionReport,
        live_preview: LivePreviewReport,
        testnet_positions: TestnetPositionSummary,
        liquidity_decision: LiquidityDecision,
        grid_liquidity_decision: LiquidityDecision,
        spot_capital_plan: CapitalSourcingPlan,
        grid_capital_plan: CapitalSourcingPlan,
        strategy_decision: StrategyDecision,
        next_run: NextRunRecommendation,
        recommended_actions: tuple[RecommendedAction, ...],
        execution_checklist: tuple[ExecutionChecklistItem, ...],
        ai_commentary: AiCommentary,
        research: ResearchBundle,
        research_status: ResearchStatus,
        active_strategies: ActiveStrategiesReport,
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
                    "| Symbol | Side | Type | Quote USDT | Status | Available USDT | Confirmation Required | Validation |",
                    "| --- | --- | --- | ---: | --- | ---: | --- | --- |",
                ]
            )
            for order in live_preview.orders:
                lines.append(
                    "| "
                    f"{order.symbol} | {order.side} | {order.order_type} | {order.quote_amount_usdt} | "
                    f"{order.status} | {order.available_usdt} | {order.confirmation_required} | {order.validation_summary} |"
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
                    "| Name | Symbol | Range | Current Price | State | Distance Lower | Distance Upper | Recommendation |",
                    "| --- | --- | ---: | ---: | --- | ---: | ---: | --- |",
                ]
            )
            for item in active_strategies.grid_bots:
                lines.append(
                    "| "
                    f"{item.bot.name} | {item.bot.symbol} | {item.bot.range_low}-{item.bot.range_high} | "
                    f"{item.current_price if item.current_price is not None else ''} | {item.state} | "
                    f"{item.distance_to_lower_pct if item.distance_to_lower_pct is not None else ''}% | "
                    f"{item.distance_to_upper_pct if item.distance_to_upper_pct is not None else ''}% | "
                    f"{item.recommendation} |"
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
                f"| {snapshot.symbol} | {snapshot.price} | {snapshot.rsi14} | {snapshot.ema20:.2f} | {snapshot.ema50:.2f} | {snapshot.ema200:.2f} | {snapshot.trend_regime} |"
            )
        lines.extend(
            [
                "",
                "## AI Proposal",
                "",
                f"- Action: `{proposal.action}`",
                f"- Symbol: `{proposal.symbol}`",
                f"- Confidence: `{proposal.confidence}`",
                f"- Quote amount: `{proposal.quote_amount_usdt} USDT`",
                f"- Stop loss: `{proposal.stop_loss_pct}%`",
                f"- Take profit: `{proposal.take_profit_pct}%`",
                f"- Reason: {proposal.reason}",
                "",
                "## Risk Decision",
                "",
                f"- Approved: `{risk_decision.approved}`",
                f"- Reason: {risk_decision.reason}",
                f"- Adjusted quote amount: `{risk_decision.adjusted_quote_amount_usdt} USDT`",
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
                    f"- Symbol: `{grid.symbol}`",
                    f"- Reason: {grid.reason}",
                    f"- Range low: `{grid.range_low}`",
                    f"- Range high: `{grid.range_high}`",
                    f"- Grid count: `{grid.grid_count}`",
                    f"- Grid type: `{grid.grid_type}`",
                    f"- Investment: `{grid.investment_usdt} USDT`",
                    f"- Stop loss price: `{grid.stop_loss_price}`",
                    f"- Take profit price: `{grid.take_profit_price}`",
                    "",
                ]
            )
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
                "No mainnet live order, redeem, or grid bot was created. Spot Testnet execution may be present above when explicitly enabled.",
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
            f"- Needed: `{plan.needed_usdt} USDT`",
            f"- Available USDT: `{plan.available_usdt} USDT`",
            f"- Missing: `{plan.missing_usdt} USDT`",
            f"- Recommended: `{plan.recommended}`",
            f"- Summary: {plan.summary}",
        ]
        if plan.items:
            lines.extend(["", "| Asset | Value USDT | Action | Reason |", "| --- | ---: | --- | --- |"])
            for item in plan.items:
                lines.append(f"| {item.asset} | {item.value_usdt} | {item.action} | {item.reason} |")
        return lines
