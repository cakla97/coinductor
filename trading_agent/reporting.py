from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import AiCommentary, Balance, CapitalSourcingPlan, LiquidityDecision, MarketSnapshot, NextRunRecommendation, PortfolioAnalysis, RecommendedAction, ResearchBundle, ResearchStatus, RiskDecision, StrategyDecision, TradeProposal


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
        snapshots: list[MarketSnapshot],
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        liquidity_decision: LiquidityDecision,
        grid_liquidity_decision: LiquidityDecision,
        spot_capital_plan: CapitalSourcingPlan,
        grid_capital_plan: CapitalSourcingPlan,
        strategy_decision: StrategyDecision,
        next_run: NextRunRecommendation,
        recommended_actions: tuple[RecommendedAction, ...],
        ai_commentary: AiCommentary,
        research: ResearchBundle,
        research_status: ResearchStatus,
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
                "| Asset | Price USDT | Spot value | Flexible value | Locked value | Total value | Allocation | Target | Gap | Action |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for asset in portfolio_analysis.assets:
            target = "" if asset.target_pct is None else f"{asset.target_pct}%"
            gap = "" if asset.gap_pct is None else f"{asset.gap_pct:+}%"
            lines.append(
                "| "
                f"{asset.asset} | {asset.price_usdt} | {asset.spot_value_usdt} | {asset.flexible_value_usdt} | "
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
                "No live order, redeem, or grid bot was created. MVP is running in dry-run/recommend-only mode.",
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
