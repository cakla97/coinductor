from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Balance:
    asset: str
    spot_free: Decimal
    spot_locked: Decimal = Decimal("0")
    flexible_amount: Decimal = Decimal("0")
    locked_amount: Decimal = Decimal("0")


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    price: Decimal
    ema20: Decimal
    ema50: Decimal
    ema200: Decimal
    rsi14: Decimal
    atr14: Decimal
    volume_trend: str
    trend_regime: str


@dataclass(frozen=True)
class TradeProposal:
    symbol: str
    action: str
    confidence: Decimal
    quote_amount_usdt: Decimal
    stop_loss_pct: Decimal
    take_profit_pct: Decimal
    reason: str


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str
    adjusted_quote_amount_usdt: Decimal


@dataclass(frozen=True)
class LiquidityDecision:
    approved: bool
    reason: str
    redeem_asset: str | None
    redeem_amount: Decimal


@dataclass(frozen=True)
class GridRecommendation:
    recommended: bool
    symbol: str | None
    reason: str
    range_low: Decimal
    range_high: Decimal
    grid_count: int
    grid_type: str
    investment_usdt: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal
    manual_steps: tuple[str, ...]


@dataclass(frozen=True)
class StrategyDecision:
    decision_type: str
    priority: str
    summary: str
    spot_trade: TradeProposal | None
    grid: GridRecommendation | None
    rebalancing_note: str | None


@dataclass(frozen=True)
class NextRunRecommendation:
    run_again_in_hours: int
    urgency: str
    reason: str
    triggers: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioAssetValuation:
    asset: str
    role: str
    price_usdt: Decimal
    spot_value_usdt: Decimal
    flexible_value_usdt: Decimal
    locked_value_usdt: Decimal
    total_value_usdt: Decimal
    allocation_pct: Decimal
    target_pct: Decimal | None
    gap_pct: Decimal | None
    rebalance_action: str


@dataclass(frozen=True)
class PortfolioAnalysis:
    total_value_usdt: Decimal
    spot_value_usdt: Decimal
    flexible_value_usdt: Decimal
    locked_value_usdt: Decimal
    liquid_value_usdt: Decimal
    locked_pct: Decimal
    assets: tuple[PortfolioAssetValuation, ...]
    unpriced_assets: tuple[str, ...]
    ignored_internal_assets: tuple[str, ...]
    rebalance_summary: str
    liquidity_summary: str


@dataclass(frozen=True)
class CapitalSourcePlanItem:
    asset: str
    action: str
    value_usdt: Decimal
    reason: str


@dataclass(frozen=True)
class CapitalSourcingPlan:
    needed_usdt: Decimal
    available_usdt: Decimal
    missing_usdt: Decimal
    recommended: bool
    summary: str
    items: tuple[CapitalSourcePlanItem, ...]


@dataclass(frozen=True)
class RecommendedAction:
    priority: str
    action: str
    reason: str


@dataclass(frozen=True)
class ExecutionChecklistItem:
    priority: str
    step: str
    detail: str


@dataclass(frozen=True)
class ConfigIssue:
    severity: str
    path: str
    message: str


@dataclass(frozen=True)
class ConfigValidationResult:
    issues: tuple[ConfigIssue, ...]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "ERROR" for issue in self.issues)


@dataclass(frozen=True)
class AiCommentary:
    enabled: bool
    summary: str
    risks: tuple[str, ...]
    watchlist: tuple[str, ...]
    raw_response: str


@dataclass(frozen=True)
class ResearchNote:
    source: str
    title: str
    content: str


@dataclass(frozen=True)
class ResearchBundle:
    enabled: bool
    notes: tuple[ResearchNote, ...]


@dataclass(frozen=True)
class ResearchRequest:
    path: str
    title: str
    content: str


@dataclass(frozen=True)
class ResearchStatus:
    enabled: bool
    notes_count: int
    is_fresh: bool
    latest_note_age_hours: Decimal | None
    request: ResearchRequest | None
    summary: str


@dataclass(frozen=True)
class ActiveGridBot:
    name: str
    symbol: str
    range_low: Decimal
    range_high: Decimal
    investment_usdt: Decimal
    created_at: str
    status: str
    notes: str


@dataclass(frozen=True)
class ActiveGridEvaluation:
    bot: ActiveGridBot
    current_price: Decimal | None
    state: str
    distance_to_lower_pct: Decimal | None
    distance_to_upper_pct: Decimal | None
    recommendation: str


@dataclass(frozen=True)
class ActiveStrategiesReport:
    enabled: bool
    grid_bots: tuple[ActiveGridEvaluation, ...]
    summary: str


@dataclass(frozen=True)
class PaperOrder:
    intent_id: str
    symbol: str
    side: str
    quote_amount_usdt: Decimal
    simulated_price: Decimal
    simulated_quantity: Decimal
    fee_usdt: Decimal
    slippage_usdt: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal
    status: str
    reason: str


@dataclass(frozen=True)
class PaperExecutionReport:
    enabled: bool
    orders: tuple[PaperOrder, ...]
    summary: str


@dataclass(frozen=True)
class TestnetOrderRequest:
    symbol: str
    side: str
    order_type: str
    quote_order_qty: Decimal | None
    quantity: Decimal | None
    price: Decimal | None
    time_in_force: str | None
    client_order_id: str


@dataclass(frozen=True)
class TestnetOrderResult:
    submitted: bool
    status: str
    message: str
    response: str


@dataclass(frozen=True)
class SymbolRules:
    symbol: str
    status: str
    base_asset: str
    quote_asset: str
    quote_order_qty_market_allowed: bool
    min_qty: Decimal
    max_qty: Decimal
    step_size: Decimal
    min_notional: Decimal
    tick_size: Decimal


@dataclass(frozen=True)
class OrderValidation:
    approved: bool
    reason: str
    adjusted_quote_amount_usdt: Decimal


@dataclass(frozen=True)
class TestnetExecutedOrder:
    intent_id: str
    symbol: str
    side: str
    quote_amount_usdt: Decimal
    client_order_id: str
    submitted: bool
    status: str
    executed_quantity: Decimal
    cumulative_quote_qty: Decimal
    order_id: str
    queried_status: str
    validation_summary: str
    message: str


@dataclass(frozen=True)
class TestnetExecutionReport:
    enabled: bool
    orders: tuple[TestnetExecutedOrder, ...]
    summary: str


@dataclass(frozen=True)
class TestnetPositionCycle:
    symbol: str
    buy_order_id: str
    sell_order_id: str | None
    buy_quote_usdt: Decimal
    sell_quote_usdt: Decimal | None
    quantity: Decimal
    status: str
    pnl_usdt: Decimal | None


@dataclass(frozen=True)
class TestnetPositionSummary:
    enabled: bool
    open_positions: tuple[TestnetPositionCycle, ...]
    closed_positions: tuple[TestnetPositionCycle, ...]
    total_realized_pnl_usdt: Decimal
    summary: str


@dataclass(frozen=True)
class AgentRunResult:
    run_id: int
    status: str
    report_path: str
