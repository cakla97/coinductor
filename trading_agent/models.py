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
class AiCommentary:
    enabled: bool
    summary: str
    risks: tuple[str, ...]
    watchlist: tuple[str, ...]
    raw_response: str


@dataclass(frozen=True)
class AgentRunResult:
    run_id: int
    status: str
    report_path: str
