from __future__ import annotations

from decimal import Decimal

from .active_strategies import ActiveStrategiesTracker
from .ai_analyst import AiAnalyst
from .binance_client import BinanceClient
from .capital_sourcing import CapitalSourcingAdvisor
from .config import AppConfig
from .earn_manager import EarnLiquidityManager
from .execution_checklist import ExecutionChecklistBuilder
from .grid_advisor import GridBotAdvisor
from .models import AgentRunResult, LiquidityDecision
from .next_run import NextRunAdvisor
from .paper_executor import PaperExecutor
from .portfolio_analyzer import PortfolioAnalyzer
from .recommended_actions import RecommendedActionsBuilder
from .rebalance_planner import RebalancePlanner
from .reporting import Reporter
from .research import ResearchLoader
from .risk_engine import RiskEngine
from .storage import Storage
from .strategy_decision import StrategyDecisionEngine
from .testnet_executor import TestnetExecutor


class AgentRunner:
    def __init__(self, config: AppConfig):
        self.config = config
        self.storage = Storage(config.database_path)
        self.client = BinanceClient(config.raw)
        self.ai = AiAnalyst(config.raw)
        self.risk = RiskEngine(config.raw)
        self.earn = EarnLiquidityManager(config.raw)
        self.grid = GridBotAdvisor(config.raw)
        self.portfolio = PortfolioAnalyzer(config.raw)
        self.capital_sourcing = CapitalSourcingAdvisor(config.raw)
        self.rebalance_planner = RebalancePlanner(config.raw)
        self.strategy = StrategyDecisionEngine()
        self.next_run = NextRunAdvisor()
        self.actions = RecommendedActionsBuilder()
        self.checklist = ExecutionChecklistBuilder()
        self.paper = PaperExecutor(config.raw)
        self.testnet = TestnetExecutor(config.raw)
        self.research = ResearchLoader(config.raw)
        self.active_strategies = ActiveStrategiesTracker(config.raw)
        self.reporter = Reporter(config.reports_dir, keep_last=int(config.raw.get("reports", {}).get("keep_last", 30)))

    def run(self) -> AgentRunResult:
        run_id = self.storage.start_run(self.config.mode)
        try:
            balances = self.client.get_balances()
            snapshots = self.client.get_market_snapshots(self.config.allowed_symbols)
            active_strategies_report = self.active_strategies.evaluate(snapshots)
            portfolio_assets = sorted(
                {balance.asset for balance in balances}
                | {asset.upper() for asset in self.config.raw.get("portfolio", {}).get("tracked_assets", [])}
            )
            asset_prices = self.client.get_asset_prices_usdt(portfolio_assets)
            portfolio_analysis = self.portfolio.analyze(balances, asset_prices)
            rebalance_plan = self.rebalance_planner.plan(portfolio_analysis)
            research_bundle = self.research.load()
            research_status = self.research.status_and_request(portfolio_analysis)
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
            grid_recommendation = self.grid.recommend(snapshots)
            if grid_recommendation.recommended:
                grid_liquidity_decision = self.earn.ensure_quote_liquidity(
                    balances=balances,
                    quote_asset="USDT",
                    required_amount=grid_recommendation.investment_usdt,
                )
                grid_capital_plan = self.capital_sourcing.plan(balances, portfolio_analysis, grid_recommendation.investment_usdt)
            else:
                grid_liquidity_decision = LiquidityDecision(False, "No grid recommendation requires liquidity.", None, Decimal("0"))
                grid_capital_plan = self.capital_sourcing.plan(balances, portfolio_analysis, Decimal("0"))
            spot_capital_plan = self.capital_sourcing.plan(balances, portfolio_analysis, risk_decision.adjusted_quote_amount_usdt)
            paper_execution = self.paper.simulate_spot(
                proposal,
                risk_decision,
                snapshots,
                existing_intents=self.storage.get_existing_paper_intents(),
            )
            testnet_execution = self.testnet.execute_spot_proposal(
                proposal=proposal,
                risk_decision=risk_decision,
                existing_intents=self.storage.get_existing_testnet_intents(),
                confirm=str(self.config.raw.get("_runtime", {}).get("testnet_confirm", "")),
            )
            strategy_decision = self.strategy.decide(proposal, risk_decision, grid_recommendation)
            next_run_recommendation = self.next_run.recommend(strategy_decision)
            recommended_actions = self.actions.build(
                strategy_decision=strategy_decision,
                risk_decision=risk_decision,
                grid_recommendation=grid_recommendation,
                spot_capital_plan=spot_capital_plan,
                grid_capital_plan=grid_capital_plan,
                next_run=next_run_recommendation,
                active_strategies=active_strategies_report,
            )
            execution_checklist = self.checklist.build(
                proposal=proposal,
                risk_decision=risk_decision,
                liquidity_decision=liquidity_decision,
                grid_liquidity_decision=grid_liquidity_decision,
                spot_capital_plan=spot_capital_plan,
                grid_capital_plan=grid_capital_plan,
                grid_recommendation=grid_recommendation,
                strategy_decision=strategy_decision,
                research_status=research_status,
            )
            ai_commentary = self.ai.comment_on_portfolio(
                portfolio=portfolio_analysis,
                snapshots=snapshots,
                proposal=proposal,
                risk_decision=risk_decision,
                grid_recommendation=grid_recommendation,
                spot_capital_plan=spot_capital_plan,
                grid_capital_plan=grid_capital_plan,
                strategy_decision=strategy_decision,
                next_run=next_run_recommendation,
                recommended_actions=recommended_actions,
                research=research_bundle,
                research_status=research_status,
                active_strategies=active_strategies_report,
            )

            self.storage.save_balances(run_id, balances)
            self.storage.save_portfolio_analysis(run_id, portfolio_analysis)
            self.storage.save_market_snapshots(run_id, snapshots)
            self.storage.save_proposal(run_id, proposal)
            self.storage.save_risk_decision(run_id, risk_decision)
            self.storage.save_paper_execution(run_id, paper_execution)
            self.storage.save_testnet_execution(run_id, testnet_execution)
            self.storage.save_grid_recommendation(run_id, grid_recommendation)
            self.storage.save_capital_sourcing_plan(run_id, "SPOT_TRADE", spot_capital_plan)
            self.storage.save_capital_sourcing_plan(run_id, "GRID_BOT", grid_capital_plan)
            self.storage.save_strategy_decision(run_id, strategy_decision)
            self.storage.save_next_run_recommendation(run_id, next_run_recommendation)
            self.storage.save_recommended_actions(run_id, recommended_actions)
            self.storage.save_execution_checklist(run_id, execution_checklist)
            self.storage.save_ai_commentary(run_id, ai_commentary)
            self.storage.save_research_notes(run_id, research_bundle)
            self.storage.save_research_status(run_id, research_status)
            self.storage.save_active_strategies(run_id, active_strategies_report)
            testnet_positions = self.storage.get_testnet_position_summary()
            report_path = self.reporter.write_report(
                run_id=run_id,
                mode=self.config.mode,
                balances=balances,
                portfolio_analysis=portfolio_analysis,
                rebalance_plan=rebalance_plan,
                snapshots=snapshots,
                proposal=proposal,
                risk_decision=risk_decision,
                paper_execution=paper_execution,
                testnet_execution=testnet_execution,
                testnet_positions=testnet_positions,
                liquidity_decision=liquidity_decision,
                grid_liquidity_decision=grid_liquidity_decision,
                spot_capital_plan=spot_capital_plan,
                grid_capital_plan=grid_capital_plan,
                strategy_decision=strategy_decision,
                next_run=next_run_recommendation,
                recommended_actions=recommended_actions,
                execution_checklist=execution_checklist,
                ai_commentary=ai_commentary,
                research=research_bundle,
                research_status=research_status,
                active_strategies=active_strategies_report,
            )
            self.storage.cleanup_old_runs(int(self.config.raw.get("retention", {}).get("keep_database_runs", 500)))
            status = "OK"
            self.storage.finish_run(run_id, status, f"Report written to {report_path}")
            return AgentRunResult(run_id=run_id, status=status, report_path=str(report_path))
        except Exception as exc:
            self.storage.finish_run(run_id, "ERROR", str(exc))
            raise
