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
class AgentRunResult:
    run_id: int
    status: str
    report_path: str

