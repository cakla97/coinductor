from __future__ import annotations

from decimal import Decimal

from .active_strategies import ActiveStrategiesTracker
from .ai_analyst import AiAnalyst
from .binance_clients import create_binance_client
from .capital_sourcing import CapitalSourcingAdvisor
from .config import AppConfig
from .earn_manager import EarnLiquidityManager
from .dust_sourcing import DustSourcingAdvisor
from .execution_checklist import ExecutionChecklistBuilder
from .grid_advisor import GridBotAdvisor
from .live_exit_preview import LiveExitPreviewBuilder
from .live_preview import LivePreviewExecutor
from .market_research import MarketResearchCollector
from .models import AgentRunResult, LiquidityDecision, OcoStatusReport
from .run_phases import (
    CapitalPlan,
    ExecutionPreviews,
    MarketView,
    PortfolioPlans,
    PositionProtection,
    ResearchView,
    RunSummary,
    TradeDecision,
)
from .next_run import NextRunAdvisor
from .oco_protection_preview import OcoProtectionPreviewBuilder
from .oco_status_sync import OcoStatusSynchronizer
from .paper_executor import PaperExecutor
from .portfolio_analyzer import PortfolioAnalyzer
from .recommended_actions import RecommendedActionsBuilder
from .rebalance_planner import RebalancePlanner
from .rebalancing_bot_advisor import RebalancingBotAdvisor
from .reporting import Reporter
from .research import ResearchLoader
from .risk_engine import RiskEngine
from .runtime_flags import RuntimeFlags
from .shadow_evaluator import ShadowEvaluator
from .storage import Storage
from .strategy_decision import StrategyDecisionEngine
from .testnet_executor import TestnetExecutor
from .trading_bankroll import TradingBankrollAdvisor


class AgentRunner:
    def __init__(self, config: AppConfig):
        self.config = config
        # Snapshotted once: the CLI and the desktop set these before building the
        # runner, and nothing may grant a run more authority mid-flight.
        self.runtime = RuntimeFlags.from_config(config.raw)
        self.storage = Storage(config.database_path)
        self.client = create_binance_client(config.raw)
        self.ai = AiAnalyst(config.raw)
        self.risk = RiskEngine(config.raw)
        self.shadow = ShadowEvaluator(config.raw, self.storage, self.client)
        self.earn = EarnLiquidityManager(config.raw)
        self.dust = DustSourcingAdvisor(config.raw)
        self.grid = GridBotAdvisor(config.raw)
        self.portfolio = PortfolioAnalyzer(config.raw)
        self.capital_sourcing = CapitalSourcingAdvisor(config.raw)
        self.rebalance_planner = RebalancePlanner(config.raw)
        self.rebalancing_bot = RebalancingBotAdvisor(config.raw)
        self.strategy = StrategyDecisionEngine()
        self.next_run = NextRunAdvisor()
        self.actions = RecommendedActionsBuilder()
        self.checklist = ExecutionChecklistBuilder()
        self.paper = PaperExecutor(config.raw)
        self.testnet = TestnetExecutor(config.raw)
        self.live_preview = LivePreviewExecutor(config.raw)
        self.market_research = MarketResearchCollector(config.raw, self.client)
        self.live_exit_preview = LiveExitPreviewBuilder(config.raw)
        self.oco_protection_preview = OcoProtectionPreviewBuilder(config.raw)
        self.oco_status = OcoStatusSynchronizer(config.raw, self.storage)
        self.bankroll = TradingBankrollAdvisor(config.raw)
        self.research = ResearchLoader(config.raw)
        self.active_strategies = ActiveStrategiesTracker(config.raw)
        self.reporter = Reporter(config.reports_dir, keep_last=int(config.raw.get("reports", {}).get("keep_last", 30)))

    def run(self) -> AgentRunResult:
        run_id = self.storage.start_run(self.config.mode)
        try:
            market = self._collect_market_view()
            portfolio_plans = self._plan_portfolio(market)
            research = self._load_research(market)
            oco_status_report = self.oco_status.sync(run_id)
            decision = self._decide_trade(run_id, market)
            capital = self._plan_capital(run_id, market, decision)
            previews = self._preview_executions(market, decision, capital)
            summary = self._summarise(run_id, market, portfolio_plans, research, decision, capital, previews)

            self._persist(run_id, market, portfolio_plans, research, decision, capital, previews, summary, oco_status_report)
            protection = self._build_position_protection(market)
            self.storage.save_oco_protection_preview(run_id, protection.oco_preview)

            report_path = self._write_report(
                run_id, market, portfolio_plans, research, decision, capital, previews, summary, protection, oco_status_report
            )
            self.storage.cleanup_old_runs(int(self.config.raw.get("retention", {}).get("keep_database_runs", 500)))
            status = "OK"
            self.storage.finish_run(run_id, status, f"Report written to {report_path}")
            return AgentRunResult(run_id=run_id, status=status, report_path=str(report_path))
        except Exception as exc:
            self.storage.finish_run(run_id, "ERROR", str(exc))
            raise

    # ------------------------------------------------------------------
    # Phases, in the order run() calls them.
    # ------------------------------------------------------------------

    def _collect_market_view(self) -> MarketView:
        balances = self.client.get_balances()
        snapshots = self.client.get_market_snapshots(self.config.allowed_symbols)
        market_research_report = self.market_research.collect(snapshots)
        portfolio_assets = sorted(
            {balance.asset for balance in balances}
            | {asset.upper() for asset in self.config.raw.get("portfolio", {}).get("tracked_assets", [])}
        )
        asset_prices = self.client.get_asset_prices_usdt(portfolio_assets)
        return MarketView(
            balances=balances,
            snapshots=snapshots,
            asset_prices=asset_prices,
            market_research=market_research_report,
            active_strategies=self.active_strategies.evaluate(snapshots, asset_prices),
            portfolio_analysis=self.portfolio.analyze(balances, asset_prices),
        )

    def _plan_portfolio(self, market: MarketView) -> PortfolioPlans:
        return PortfolioPlans(
            rebalance=self.rebalance_planner.plan(market.portfolio_analysis),
            rebalancing_bot=self.rebalancing_bot.recommend(market.portfolio_analysis, market.balances),
            dust=self.dust.plan(market.portfolio_analysis),
        )

    def _load_research(self, market: MarketView) -> ResearchView:
        return ResearchView(
            bundle=self.research.load(),
            status=self.research.status_and_request(market.portfolio_analysis),
        )

    def _decide_trade(self, run_id: int, market: MarketView) -> TradeDecision:
        """Ask the analyst, then let the deterministic risk engine rule on it."""
        decision_memory = self.storage.get_ai_decision_memory(self.config.raw)
        pre_trade_live_positions = self.storage.get_live_position_summary(market.snapshots, self.config.raw)
        if self.runtime.manual_override_symbol:
            proposal = self.ai.propose_manual_override(
                self.runtime.manual_override_symbol,
                market.snapshots,
                live_positions=pre_trade_live_positions,
            )
        else:
            proposal = self.ai.propose_trade(
                market.snapshots,
                live_positions=pre_trade_live_positions,
                decision_memory=decision_memory,
                market_research=market.market_research,
            )
        risk_state = self.storage.get_live_risk_state(run_id, self.config.raw)
        return TradeDecision(
            decision_memory=decision_memory,
            pre_trade_live_positions=pre_trade_live_positions,
            proposal=proposal,
            risk_state=risk_state,
            risk_decision=self.risk.evaluate(
                proposal=proposal,
                risk_state=risk_state,
                snapshots=market.snapshots,
                # The tactical trade is what the [risk] percentages are written
                # about, so this is where they bind. Funding is passed too, so
                # the size cannot exceed what the account can actually pay.
                portfolio_value=market.portfolio_analysis.total_value_usdt,
                spendable_quote=self.earn.spendable_quote(
                    market.balances,
                    self._live_quote_asset(),
                    redeemed_today=self.storage.get_earn_redeemed_today(run_id),
                    portfolio_value=market.portfolio_analysis.total_value_usdt,
                ),
            ),
        )

    def _plan_capital(self, run_id: int, market: MarketView, decision: TradeDecision) -> CapitalPlan:
        risk_decision = decision.risk_decision
        # What the day's Earn allowance has already spent. Read once and
        # passed down, so the liquidity check, the redeem plan and the grid
        # check all size against the same remaining allowance rather than
        # each rediscovering it.
        redeemed_today = self.storage.get_earn_redeemed_today(run_id)
        portfolio_value = market.portfolio_analysis.total_value_usdt
        if risk_decision.approved:
            liquidity_decision = self.earn.ensure_quote_liquidity(
                balances=market.balances,
                quote_asset=self._live_quote_asset(),
                required_amount=risk_decision.adjusted_quote_amount_usdt,
                redeemed_today=redeemed_today,
                portfolio_value=portfolio_value,
            )
        else:
            liquidity_decision = LiquidityDecision(False, "Risk engine rejected proposal before liquidity check.", None, Decimal("0"))
        live_quote_cap = Decimal(
            str(self.config.raw.get("live_confirm", {}).get("max_quote_amount_usdt", risk_decision.adjusted_quote_amount_usdt))
        )
        bankroll_required = min(risk_decision.adjusted_quote_amount_usdt, live_quote_cap) if risk_decision.approved else Decimal("0")
        bankroll_report = self.bankroll.analyze(market.balances, bankroll_required)
        earn_redeem_plan = self.earn.plan_flexible_redeem(
            liquidity_decision,
            bankroll_report,
            existing_intents=self.storage.get_existing_earn_redeem_intents(),
            redeemed_today=redeemed_today,
            portfolio_value=portfolio_value,
        )
        grid_recommendation = self.grid.recommend(
            snapshots=market.snapshots,
            market_research=market.market_research,
            active_strategies=market.active_strategies,
            risk_state=decision.risk_state,
            portfolio_value_usdt=market.portfolio_analysis.total_value_usdt,
        )
        if grid_recommendation.recommended:
            grid_liquidity_decision = self.earn.ensure_quote_liquidity(
                balances=market.balances,
                quote_asset=self._live_quote_asset(),
                required_amount=grid_recommendation.investment_usdt,
                redeemed_today=redeemed_today,
                portfolio_value=portfolio_value,
            )
            grid_capital_plan = self.capital_sourcing.plan(
                market.balances, market.portfolio_analysis, grid_recommendation.investment_usdt
            )
        else:
            grid_liquidity_decision = LiquidityDecision(False, "No grid recommendation requires liquidity.", None, Decimal("0"))
            grid_capital_plan = self.capital_sourcing.plan(market.balances, market.portfolio_analysis, Decimal("0"))
        return CapitalPlan(
            liquidity_decision=liquidity_decision,
            bankroll=bankroll_report,
            earn_redeem_plan=earn_redeem_plan,
            grid_recommendation=grid_recommendation,
            grid_liquidity_decision=grid_liquidity_decision,
            grid_capital_plan=grid_capital_plan,
            spot_capital_plan=self.capital_sourcing.plan(
                market.balances, market.portfolio_analysis, risk_decision.adjusted_quote_amount_usdt
            ),
        )

    def _preview_executions(self, market: MarketView, decision: TradeDecision, capital: CapitalPlan) -> ExecutionPreviews:
        """Build the three execution paths. Each one gates itself; none submits here."""
        return ExecutionPreviews(
            paper=self.paper.simulate_spot(
                decision.proposal,
                decision.risk_decision,
                market.snapshots,
                existing_intents=self.storage.get_existing_paper_intents(),
            ),
            testnet=self.testnet.execute_spot_proposal(
                proposal=decision.proposal,
                risk_decision=decision.risk_decision,
                existing_intents=self.storage.get_existing_testnet_intents(),
                confirm=self.runtime.testnet_confirm,
            ),
            live=self.live_preview.preview_spot_proposal(
                decision.proposal,
                decision.risk_decision,
                capital.bankroll,
                existing_intents=self.storage.get_existing_live_intents(),
            ),
        )

    def _summarise(
        self,
        run_id: int,
        market: MarketView,
        plans: PortfolioPlans,
        research: ResearchView,
        decision: TradeDecision,
        capital: CapitalPlan,
        previews: ExecutionPreviews,
    ) -> RunSummary:
        strategy_decision = self.strategy.decide(decision.proposal, decision.risk_decision, capital.grid_recommendation)
        next_run_recommendation = self.next_run.recommend(strategy_decision)
        recommended_actions = self.actions.build(
            strategy_decision=strategy_decision,
            risk_decision=decision.risk_decision,
            grid_recommendation=capital.grid_recommendation,
            rebalancing_bot_recommendation=plans.rebalancing_bot,
            spot_capital_plan=capital.spot_capital_plan,
            grid_capital_plan=capital.grid_capital_plan,
            next_run=next_run_recommendation,
            active_strategies=market.active_strategies,
        )
        execution_checklist = self.checklist.build(
            proposal=decision.proposal,
            risk_decision=decision.risk_decision,
            liquidity_decision=capital.liquidity_decision,
            grid_liquidity_decision=capital.grid_liquidity_decision,
            spot_capital_plan=capital.spot_capital_plan,
            grid_capital_plan=capital.grid_capital_plan,
            grid_recommendation=capital.grid_recommendation,
            rebalancing_bot_recommendation=plans.rebalancing_bot,
            strategy_decision=strategy_decision,
            research_status=research.status,
            trading_bankroll=capital.bankroll,
            earn_redeem_plan=capital.earn_redeem_plan,
            live_preview=previews.live,
        )
        ai_commentary = self.ai.comment_on_portfolio(
            portfolio=market.portfolio_analysis,
            snapshots=market.snapshots,
            proposal=decision.proposal,
            risk_decision=decision.risk_decision,
            grid_recommendation=capital.grid_recommendation,
            rebalancing_bot_recommendation=plans.rebalancing_bot,
            spot_capital_plan=capital.spot_capital_plan,
            grid_capital_plan=capital.grid_capital_plan,
            strategy_decision=strategy_decision,
            next_run=next_run_recommendation,
            recommended_actions=recommended_actions,
            research=research.bundle,
            research_status=research.status,
            active_strategies=market.active_strategies,
            decision_memory=decision.decision_memory,
            market_research=market.market_research,
        )
        return RunSummary(
            strategy_decision=strategy_decision,
            next_run=next_run_recommendation,
            recommended_actions=recommended_actions,
            execution_checklist=execution_checklist,
            ai_commentary=ai_commentary,
            shadow_evaluation=self.shadow.process(run_id, decision.proposal, market.snapshots),
        )

    def _persist(
        self,
        run_id: int,
        market: MarketView,
        plans: PortfolioPlans,
        research: ResearchView,
        decision: TradeDecision,
        capital: CapitalPlan,
        previews: ExecutionPreviews,
        summary: RunSummary,
        oco_status_report: OcoStatusReport,
    ) -> None:
        self.storage.save_balances(run_id, market.balances)
        self.storage.save_portfolio_analysis(run_id, market.portfolio_analysis)
        self.storage.save_market_snapshots(run_id, market.snapshots)
        self.storage.save_market_research(run_id, market.market_research)
        self.storage.save_proposal(run_id, decision.proposal)
        self.storage.save_live_risk_state(run_id, decision.risk_state)
        self.storage.save_risk_decision(run_id, decision.risk_decision)
        self.storage.save_trading_bankroll_report(run_id, capital.bankroll)
        self.storage.save_earn_redeem_plan(run_id, capital.earn_redeem_plan)
        self.storage.save_paper_execution(run_id, previews.paper)
        self.storage.save_testnet_execution(run_id, previews.testnet)
        self.storage.save_live_preview(run_id, previews.live)
        self.storage.save_grid_recommendation(run_id, capital.grid_recommendation)
        self.storage.save_rebalancing_bot_recommendation(run_id, plans.rebalancing_bot)
        self.storage.save_capital_sourcing_plan(run_id, "SPOT_TRADE", capital.spot_capital_plan)
        self.storage.save_capital_sourcing_plan(run_id, "GRID_BOT", capital.grid_capital_plan)
        if plans.rebalancing_bot.funding_plan is not None:
            self.storage.save_capital_sourcing_plan(run_id, "REBALANCING_BOT", plans.rebalancing_bot.funding_plan)
        self.storage.save_strategy_decision(run_id, summary.strategy_decision)
        self.storage.save_next_run_recommendation(run_id, summary.next_run)
        self.storage.save_recommended_actions(run_id, summary.recommended_actions)
        self.storage.save_execution_checklist(run_id, summary.execution_checklist)
        self.storage.save_ai_commentary(run_id, summary.ai_commentary)
        self.storage.save_research_notes(run_id, research.bundle)
        self.storage.save_research_status(run_id, research.status)
        self.storage.save_active_strategies(run_id, market.active_strategies)
        self.storage.save_oco_status_report(run_id, oco_status_report)

    def _build_position_protection(self, market: MarketView) -> PositionProtection:
        """Read positions back from the journal now that this run's rows are in."""
        live_positions = self.storage.get_live_position_summary(market.snapshots, self.config.raw)
        return PositionProtection(
            testnet_positions=self.storage.get_testnet_position_summary(),
            live_positions=live_positions,
            exit_preview=self.live_exit_preview.build(live_positions, market.balances),
            oco_preview=self.oco_protection_preview.build(
                live_positions,
                market.balances,
                existing_intents=self.storage.get_existing_oco_intents(),
            ),
        )

    def _write_report(
        self,
        run_id: int,
        market: MarketView,
        plans: PortfolioPlans,
        research: ResearchView,
        decision: TradeDecision,
        capital: CapitalPlan,
        previews: ExecutionPreviews,
        summary: RunSummary,
        protection: PositionProtection,
        oco_status_report: OcoStatusReport,
    ):
        return self.reporter.write_report(
            run_id=run_id,
            mode=self.config.mode,
            balances=market.balances,
            portfolio_analysis=market.portfolio_analysis,
            rebalance_plan=plans.rebalance,
            rebalancing_bot_recommendation=plans.rebalancing_bot,
            snapshots=market.snapshots,
            market_research=market.market_research,
            proposal=decision.proposal,
            risk_state=decision.risk_state,
            risk_decision=decision.risk_decision,
            trading_bankroll=capital.bankroll,
            earn_redeem_plan=capital.earn_redeem_plan,
            paper_execution=previews.paper,
            testnet_execution=previews.testnet,
            live_preview=previews.live,
            testnet_positions=protection.testnet_positions,
            live_positions=protection.live_positions,
            live_exit_preview=protection.exit_preview,
            oco_protection_preview=protection.oco_preview,
            oco_status=oco_status_report,
            liquidity_decision=capital.liquidity_decision,
            grid_liquidity_decision=capital.grid_liquidity_decision,
            spot_capital_plan=capital.spot_capital_plan,
            grid_capital_plan=capital.grid_capital_plan,
            dust_plan=plans.dust,
            strategy_decision=summary.strategy_decision,
            next_run=summary.next_run,
            recommended_actions=summary.recommended_actions,
            execution_checklist=summary.execution_checklist,
            ai_commentary=summary.ai_commentary,
            research=research.bundle,
            research_status=research.status,
            active_strategies=market.active_strategies,
            decision_memory=decision.decision_memory,
            shadow_evaluation=summary.shadow_evaluation,
        )

    def _live_quote_asset(self) -> str:
        return str(self.config.raw.get("live_confirm", {}).get("quote_asset", "USDT")).upper()
