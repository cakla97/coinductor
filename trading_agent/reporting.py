from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import Balance, LiquidityDecision, MarketSnapshot, NextRunRecommendation, PortfolioAnalysis, RiskDecision, StrategyDecision, TradeProposal


class Reporter:
    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir
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
        strategy_decision: StrategyDecision,
        next_run: NextRunRecommendation,
    ) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = self.reports_dir / f"{timestamp}_run-{run_id}.md"
        lines = [
            f"# Trading Agent Report #{run_id}",
            "",
            f"- Mode: `{mode}`",
            f"- Generated: `{timestamp}`",
            "",
            "## Executive Summary",
            "",
            f"- Total portfolio value: `{portfolio_analysis.total_value_usdt} USDT`",
            f"- Liquid value: `{portfolio_analysis.liquid_value_usdt} USDT`",
            f"- Locked value: `{portfolio_analysis.locked_value_usdt} USDT` (`{portfolio_analysis.locked_pct}%`)",
            f"- Rebalance: {portfolio_analysis.rebalance_summary}",
            f"- Liquidity: {portfolio_analysis.liquidity_summary}",
            "",
            "## Portfolio",
            "",
            "| Asset | Spot free | Flexible | Locked |",
            "| --- | ---: | ---: | ---: |",
        ]
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
        return path
