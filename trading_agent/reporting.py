from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import Balance, LiquidityDecision, MarketSnapshot, RiskDecision, TradeProposal


class Reporter:
    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def write_report(
        self,
        run_id: int,
        mode: str,
        balances: list[Balance],
        snapshots: list[MarketSnapshot],
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        liquidity_decision: LiquidityDecision,
    ) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = self.reports_dir / f"{timestamp}_run-{run_id}.md"
        lines = [
            f"# Trading Agent Report #{run_id}",
            "",
            f"- Mode: `{mode}`",
            f"- Generated: `{timestamp}`",
            "",
            "## Portfolio",
            "",
            "| Asset | Spot free | Flexible | Locked |",
            "| --- | ---: | ---: | ---: |",
        ]
        for balance in balances:
            lines.append(f"| {balance.asset} | {balance.spot_free} | {balance.flexible_amount} | {balance.locked_amount} |")
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
                "## Execution",
                "",
                "No live order was sent. MVP is running in dry-run/simulated mode.",
                "",
            ]
        )
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

