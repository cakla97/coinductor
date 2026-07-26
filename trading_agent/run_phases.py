"""Value bundles handed between the phases of a single agent run.

AgentRunner.run() used to keep roughly thirty locals alive at once, which made
the order of operations impossible to see. These frozen bundles give each phase
one thing to return and the next phase one thing to accept. They are plumbing
for the orchestrator, not domain models: everything inside them is defined in
``models.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .models import (
    ActiveStrategiesReport,
    AiCommentary,
    AiDecisionMemory,
    Balance,
    CapitalSourcingPlan,
    DustConversionPlan,
    EarnRedeemPlan,
    ExecutionChecklistItem,
    GridRecommendation,
    LiquidityDecision,
    LiveExitPreviewReport,
    LivePositionSummary,
    LivePreviewReport,
    LiveRiskState,
    MarketResearchReport,
    MarketSnapshot,
    NextRunRecommendation,
    OcoProtectionPreviewReport,
    PaperExecutionReport,
    PortfolioAnalysis,
    RebalancePlan,
    RebalancingBotRecommendation,
    RecommendedAction,
    ResearchBundle,
    ResearchStatus,
    RiskDecision,
    ShadowEvaluationReport,
    StrategyDecision,
    TestnetExecutionReport,
    TestnetPositionSummary,
    TradeProposal,
    TradingBankrollReport,
)


@dataclass(frozen=True)
class MarketView:
    """What the exchange looks like right now, plus the derived portfolio state."""

    balances: list[Balance]
    snapshots: list[MarketSnapshot]
    asset_prices: dict[str, Decimal]
    market_research: MarketResearchReport
    portfolio_analysis: PortfolioAnalysis
    active_strategies: ActiveStrategiesReport


@dataclass(frozen=True)
class ResearchView:
    """Operator-supplied research notes and whether a refresh is due."""

    bundle: ResearchBundle
    status: ResearchStatus


@dataclass(frozen=True)
class TradeDecision:
    """The analyst's proposal and the deterministic verdict on it.

    ``risk_decision`` is what actually governs everything downstream; the
    proposal on its own carries no authority.
    """

    decision_memory: AiDecisionMemory
    pre_trade_live_positions: LivePositionSummary
    proposal: TradeProposal
    risk_state: LiveRiskState
    risk_decision: RiskDecision


@dataclass(frozen=True)
class PortfolioPlans:
    """Allocation housekeeping derived purely from the current portfolio."""

    rebalance: RebalancePlan
    rebalancing_bot: RebalancingBotRecommendation
    dust: DustConversionPlan


@dataclass(frozen=True)
class CapitalPlan:
    """Where the money for the approved actions would come from."""

    liquidity_decision: LiquidityDecision
    bankroll: TradingBankrollReport
    earn_redeem_plan: EarnRedeemPlan
    grid_recommendation: GridRecommendation
    grid_liquidity_decision: LiquidityDecision
    grid_capital_plan: CapitalSourcingPlan
    spot_capital_plan: CapitalSourcingPlan


@dataclass(frozen=True)
class ExecutionPreviews:
    """Simulated and gated execution paths. None of these submit on their own."""

    paper: PaperExecutionReport
    testnet: TestnetExecutionReport
    live: LivePreviewReport


@dataclass(frozen=True)
class RunSummary:
    """The operator-facing conclusions drawn from everything above."""

    strategy_decision: StrategyDecision
    next_run: NextRunRecommendation
    recommended_actions: tuple[RecommendedAction, ...]
    execution_checklist: tuple[ExecutionChecklistItem, ...]
    ai_commentary: AiCommentary
    shadow_evaluation: ShadowEvaluationReport


@dataclass(frozen=True)
class PositionProtection:
    """Open positions and their exit cover, read back after this run is journalled."""

    testnet_positions: TestnetPositionSummary
    live_positions: LivePositionSummary
    exit_preview: LiveExitPreviewReport
    oco_preview: OcoProtectionPreviewReport
