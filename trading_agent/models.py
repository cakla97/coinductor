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
class MarketMover:
    symbol: str
    change_24h_pct: Decimal
    quote_volume_24h: Decimal


@dataclass(frozen=True)
class SymbolMarketResearch:
    symbol: str
    change_24h_pct: Decimal
    return_7d_pct: Decimal | None
    return_30d_pct: Decimal | None
    quote_volume_24h: Decimal
    trades_24h: int
    range_24h_pct: Decimal
    atr_pct: Decimal
    price_vs_ema200_pct: Decimal
    relative_strength_vs_btc_24h_pct: Decimal | None
    support_30d: Decimal | None
    resistance_30d: Decimal | None
    volume_trend: str
    trend_regime: str


@dataclass(frozen=True)
class MarketBreadth:
    quote_asset: str
    symbols_analyzed: int
    advancing: int
    declining: int
    unchanged: int
    advance_pct: Decimal
    median_change_24h_pct: Decimal
    top_gainers: tuple[MarketMover, ...]
    top_losers: tuple[MarketMover, ...]
    top_volume: tuple[MarketMover, ...]


@dataclass(frozen=True)
class MarketResearchReport:
    enabled: bool
    status: str
    symbols: tuple[SymbolMarketResearch, ...]
    breadth: MarketBreadth | None
    errors: tuple[str, ...]
    summary: str


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
class ClosedTradeMemory:
    symbol: str
    buy_run_id: int
    entry_price: Decimal
    exit_price: Decimal
    pnl_quote: Decimal
    pnl_pct: Decimal
    entry_trend_regime: str
    entry_rsi14: Decimal | None
    entry_price_vs_ema200_pct: Decimal | None
    proposal_reason: str


@dataclass(frozen=True)
class AiDecisionMemory:
    enabled: bool
    total_closed_cycles: int
    wins: int
    losses: int
    total_realized_pnl_quote: Decimal
    recent_cycles: tuple[ClosedTradeMemory, ...]
    summary: str


@dataclass(frozen=True)
class ShadowSignal:
    run_id: int
    symbol: str
    action: str
    confidence: Decimal
    entry_price: Decimal
    horizon_hours: int
    status: str


@dataclass(frozen=True)
class ShadowEvaluation:
    signal_run_id: int
    evaluated_run_id: int
    symbol: str
    action: str
    entry_price: Decimal
    evaluation_price: Decimal
    elapsed_hours: Decimal
    symbol_return_pct: Decimal
    best_universe_symbol: str
    best_universe_return_pct: Decimal
    verdict: str
    score: str
    price_source: str


@dataclass(frozen=True)
class ShadowEvaluationReport:
    enabled: bool
    current_signal: ShadowSignal | None
    recording_status: str
    recording_message: str
    newly_evaluated: tuple[ShadowEvaluation, ...]
    pending_count: int
    completed_count: int
    correct_count: int
    wrong_count: int
    neutral_count: int
    summary: str


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str
    adjusted_quote_amount_usdt: Decimal


@dataclass(frozen=True)
class LiveRiskState:
    enabled: bool
    loss_basis_quote: Decimal
    trades_today: int
    daily_realized_pnl_quote: Decimal
    weekly_realized_pnl_quote: Decimal
    daily_loss_pct: Decimal
    weekly_loss_pct: Decimal
    consecutive_losses: int
    last_loss_at: str | None
    hours_since_last_loss: Decimal | None
    cooldown_active: bool
    daily_limit_reached: bool
    weekly_limit_reached: bool
    consecutive_loss_limit_reached: bool
    kill_switch_active: bool
    summary: str


@dataclass(frozen=True)
class LiquidityDecision:
    approved: bool
    reason: str
    redeem_asset: str | None
    redeem_amount: Decimal


@dataclass(frozen=True)
class EarnRedeemPlan:
    intent_id: str
    enabled: bool
    asset: str | None
    amount: Decimal
    status: str
    product_id: str
    redeem_type: str
    can_redeem: bool
    submitted: bool
    confirmation_required: str
    message: str


@dataclass(frozen=True)
class GridCandidateAssessment:
    symbol: str
    score: Decimal
    market_status: str
    reason: str


@dataclass(frozen=True)
class GridRecommendation:
    recommended: bool
    market_status: str
    deployment_allowed: bool
    symbol: str | None
    reason: str
    score: Decimal
    range_low: Decimal
    range_high: Decimal
    range_width_pct: Decimal
    grid_count: int
    grid_type: str
    estimated_quote_per_grid: Decimal
    estimated_grid_spacing_pct: Decimal
    investment_usdt: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal
    blockers: tuple[str, ...]
    candidate_assessments: tuple[GridCandidateAssessment, ...]
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
    source_pct_of_asset: Decimal
    remaining_value_usdt: Decimal
    remaining_pct_of_asset: Decimal
    reason: str


@dataclass(frozen=True)
class CapitalSourcingPlan:
    needed_usdt: Decimal
    available_usdt: Decimal
    missing_usdt: Decimal
    quote_asset: str
    recommended: bool
    summary: str
    items: tuple[CapitalSourcePlanItem, ...]


@dataclass(frozen=True)
class DustConversionItem:
    asset: str
    value_usdt: Decimal
    action: str
    reason: str


@dataclass(frozen=True)
class DustConversionPlan:
    enabled: bool
    quote_asset: str
    total_value_usdt: Decimal
    recommended: bool
    summary: str
    items: tuple[DustConversionItem, ...]


@dataclass(frozen=True)
class TradingBankrollReport:
    enabled: bool
    quote_asset: str
    initial_seed: Decimal
    spot_free: Decimal
    flexible_amount: Decimal
    total_quote: Decimal
    realized_pnl: Decimal
    profit_available: Decimal
    seed_capital_at_risk: Decimal
    required_amount: Decimal
    preferred_source: str
    max_profit_trade_amount: Decimal
    flexible_draw_needed: Decimal
    summary: str


@dataclass(frozen=True)
class RebalancePlanStep:
    asset: str
    symbol: str | None
    side: str
    value_usdt: Decimal
    status: str
    reason: str


@dataclass(frozen=True)
class RebalancePlan:
    enabled: bool
    preview_only: bool
    steps: tuple[RebalancePlanStep, ...]
    summary: str


@dataclass(frozen=True)
class RebalancingBotAsset:
    asset: str
    current_value_usdt: Decimal
    current_weight_pct: Decimal
    target_weight_pct: Decimal
    role: str
    status: str
    reason: str


@dataclass(frozen=True)
class RebalancingBotRecommendation:
    enabled: bool
    recommended: bool
    deployment_allowed: bool
    mode: str
    threshold_pct: Decimal
    investment_usdt: Decimal
    assets: tuple[RebalancingBotAsset, ...]
    excluded_assets: tuple[str, ...]
    blockers: tuple[str, ...]
    manual_steps: tuple[str, ...]
    summary: str
    funding_plan: CapitalSourcingPlan | None = None


@dataclass(frozen=True)
class ReadinessCheck:
    status: str
    name: str
    detail: str


@dataclass(frozen=True)
class ReadinessReport:
    checks: tuple[ReadinessCheck, ...]

    @property
    def has_blocks(self) -> bool:
        return any(check.status == "BLOCK" for check in self.checks)


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
    rebalancing_assessment: str = ""


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
    binance_bot_id: str
    symbol: str
    range_low: Decimal
    range_high: Decimal
    grid_count: int
    grid_type: str
    investment_usdt: Decimal
    entry_price: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal
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
    age_days: Decimal | None
    recommendation: str


@dataclass(frozen=True)
class ActiveRebalancingBot:
    name: str
    binance_bot_id: str
    assets: tuple[str, ...]
    target_weights_pct: tuple[Decimal, ...]
    entry_prices_usdt: tuple[Decimal, ...]
    investment_usdt: Decimal
    threshold_pct: Decimal
    created_at: str
    status: str
    notes: str


@dataclass(frozen=True)
class ActiveRebalancingEvaluation:
    bot: ActiveRebalancingBot
    current_weights_pct: tuple[Decimal, ...]
    max_drift_pct: Decimal | None
    state: str
    age_days: Decimal | None
    recommendation: str


@dataclass(frozen=True)
class ActiveStrategiesReport:
    enabled: bool
    grid_bots: tuple[ActiveGridEvaluation, ...]
    summary: str
    rebalancing_bots: tuple[ActiveRebalancingEvaluation, ...] = ()


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
class LivePositionCycle:
    intent_id: str
    symbol: str
    buy_order_id: str
    sell_order_id: str | None
    buy_quote: Decimal
    sell_quote: Decimal | None
    quantity: Decimal
    entry_price: Decimal
    current_price: Decimal | None
    current_value: Decimal | None
    pnl_quote: Decimal | None
    pnl_pct: Decimal | None
    stop_loss_price: Decimal
    take_profit_price: Decimal
    status: str
    exit_preview_status: str
    exit_preview_reason: str


@dataclass(frozen=True)
class LivePositionSummary:
    enabled: bool
    open_positions: tuple[LivePositionCycle, ...]
    closed_positions: tuple[LivePositionCycle, ...]
    total_realized_pnl_quote: Decimal
    summary: str


@dataclass(frozen=True)
class LiveExitPreviewItem:
    intent_id: str
    symbol: str
    side: str
    status: str
    reason: str
    quantity: Decimal
    adjusted_quantity: Decimal
    available_base: Decimal
    estimated_quote: Decimal
    exit_trigger: str
    confirmation_required: str


@dataclass(frozen=True)
class LiveExitPreviewReport:
    enabled: bool
    items: tuple[LiveExitPreviewItem, ...]
    summary: str


@dataclass(frozen=True)
class OcoProtectionPreviewItem:
    intent_id: str
    symbol: str
    side: str
    status: str
    reason: str
    quantity: Decimal
    adjusted_quantity: Decimal
    available_base: Decimal
    take_profit_price: Decimal
    stop_loss_stop_price: Decimal
    estimated_take_profit_quote: Decimal
    estimated_stop_quote: Decimal
    confirmation_required: str
    submitted: bool = False
    order_list_id: str = ""
    message: str = ""


@dataclass(frozen=True)
class OcoProtectionPreviewReport:
    enabled: bool
    items: tuple[OcoProtectionPreviewItem, ...]
    summary: str


@dataclass(frozen=True)
class OcoStatusItem:
    intent_id: str
    symbol: str
    order_list_id: str
    list_order_status: str
    list_status_type: str
    filled_order_id: str
    filled_quantity: Decimal
    filled_quote: Decimal
    reconciled: bool
    message: str


@dataclass(frozen=True)
class OcoStatusReport:
    enabled: bool
    items: tuple[OcoStatusItem, ...]
    summary: str


@dataclass(frozen=True)
class LiveOrderPreview:
    intent_id: str
    symbol: str
    side: str
    order_type: str
    quote_amount_usdt: Decimal
    quote_asset: str
    status: str
    validation_summary: str
    available_usdt: Decimal
    missing_usdt: Decimal
    funding_required: bool
    funding_steps: tuple[str, ...]
    confirmation_required: str
    submitted: bool = False
    order_id: str = ""
    executed_quantity: Decimal = Decimal("0")
    cumulative_quote_qty: Decimal = Decimal("0")
    message: str = ""


@dataclass(frozen=True)
class LivePreviewReport:
    enabled: bool
    orders: tuple[LiveOrderPreview, ...]
    summary: str


@dataclass(frozen=True)
class AgentRunResult:
    run_id: int
    status: str
    report_path: str


@dataclass(frozen=True)
class FirstPortfolioTrancheResult:
    intent_id: str
    mode: str
    asset: str
    symbol: str
    tranche_index: int
    tranches_total: int
    quote_amount: Decimal
    status: str
    validation_summary: str
    confirmation_required: str
    submitted: bool = False
    order_id: str = ""
    executed_quantity: Decimal = Decimal("0")
    cumulative_quote_qty: Decimal = Decimal("0")
    message: str = ""
