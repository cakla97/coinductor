from __future__ import annotations

from decimal import Decimal

from .ai_analyst import AiAnalyst
from .binance_client import BinanceClient
from .config import AppConfig
from .earn_manager import EarnLiquidityManager
from .models import AgentRunResult, LiquidityDecision
from .reporting import Reporter
from .risk_engine import RiskEngine
from .storage import Storage


class AgentRunner:
    def __init__(self, config: AppConfig):
        self.config = config
        self.storage = Storage(config.database_path)
        self.client = BinanceClient(config.raw)
        self.ai = AiAnalyst(config.raw)
        self.risk = RiskEngine(config.raw)
        self.earn = EarnLiquidityManager(config.raw)
        self.reporter = Reporter(config.reports_dir)

    def run(self) -> AgentRunResult:
        run_id = self.storage.start_run(self.config.mode)
        try:
            balances = self.client.get_balances()
            snapshots = self.client.get_market_snapshots(self.config.allowed_symbols)
            proposal = self.ai.propose_trade(snapshots)
            trades_today = self.storage.count_trades_today()
            risk_decision = self.risk.evaluate(
                proposal=proposal,
                trades_today=trades_today,
                daily_loss_pct=Decimal("0"),
                weekly_loss_pct=Decimal("0"),
            )
            if risk_decision.approved:
                liquidity_decision = self.earn.ensure_quote_liquidity(
                    balances=balances,
                    quote_asset="USDT",
                    required_amount=risk_decision.adjusted_quote_amount_usdt,
                )
            else:
                liquidity_decision = LiquidityDecision(False, "Risk engine rejected proposal before liquidity check.", None, Decimal("0"))

            self.storage.save_balances(run_id, balances)
            self.storage.save_market_snapshots(run_id, snapshots)
            self.storage.save_proposal(run_id, proposal)
            self.storage.save_risk_decision(run_id, risk_decision)
            report_path = self.reporter.write_report(
                run_id=run_id,
                mode=self.config.mode,
                balances=balances,
                snapshots=snapshots,
                proposal=proposal,
                risk_decision=risk_decision,
                liquidity_decision=liquidity_decision,
            )
            status = "OK"
            self.storage.finish_run(run_id, status, f"Report written to {report_path}")
            return AgentRunResult(run_id=run_id, status=status, report_path=str(report_path))
        except Exception as exc:
            self.storage.finish_run(run_id, "ERROR", str(exc))
            raise

