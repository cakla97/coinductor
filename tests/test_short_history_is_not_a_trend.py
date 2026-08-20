"""A pair with three weeks of candles must not read as a 200-day uptrend.

Found in a real journal. `SOXSBUSDT` was listed twenty days earlier and the run
recorded `price=46.70  ema20=45.9975  ema50=21.1660  ema200=5.2915`. Those last
two are the same number: 21.1660*50 and 5.2915*200 both equal 1058.30, because
the seed divided the sum of every candle that existed by the full period rather
than by how many there were. So `price > ema50 > ema200` held by arithmetic, the
regime came out RISK_ON, the consensus gate's `require_price_above_ema200` waved
it through, and the pair was proposed for sixteen consecutive runs.
"""

from decimal import Decimal

from trading_agent.binance_client import BinanceClient
from trading_agent.models import (
    MIN_TREND_CANDLES,
    TREND_INSUFFICIENT_HISTORY,
    LiveRiskState,
    MarketSnapshot,
    TradeProposal,
)
from trading_agent.risk_engine import RiskEngine


def _client() -> BinanceClient:
    return BinanceClient({"binance": {"api_base_url": "https://api.binance.com"}})


def _snapshot(regime: str, price="46.70", ema200="52.59") -> MarketSnapshot:
    return MarketSnapshot(
        symbol="SOXSBUSDT",
        price=Decimal(price),
        ema20=Decimal("45.99"),
        ema50=Decimal(ema200),
        ema200=Decimal(ema200),
        rsi14=Decimal("55.7"),
        atr14=Decimal("1"),
        volume_trend="rising",
        trend_regime=regime,
    )


def _proposal() -> TradeProposal:
    return TradeProposal(
        symbol="SOXSBUSDT",
        action="BUY",
        confidence=Decimal("1"),
        quote_amount_usdt=Decimal("77"),
        stop_loss_pct=Decimal("1.5"),
        take_profit_pct=Decimal("3"),
        reason="test",
    )


def _state() -> LiveRiskState:
    return LiveRiskState(
        enabled=True,
        loss_basis_quote=Decimal("1000"),
        trades_today=0,
        daily_realized_pnl_quote=Decimal("0"),
        weekly_realized_pnl_quote=Decimal("0"),
        daily_loss_pct=Decimal("0"),
        weekly_loss_pct=Decimal("0"),
        consecutive_losses=0,
        last_loss_at=None,
        hours_since_last_loss=None,
        cooldown_active=False,
        daily_limit_reached=False,
        weekly_limit_reached=False,
        consecutive_loss_limit_reached=False,
        kill_switch_active=False,
        summary="ok",
    )


def _config(**overrides) -> dict:
    config = {
        "risk": {
            "max_trades_per_day": 5,
            "max_daily_loss_pct": 100,
            "max_weekly_loss_pct": 100,
            "max_position_pct_per_asset": 100,
            "max_total_trading_capital_pct": 100,
            "max_risk_per_trade_pct": 100,
            "min_ai_confidence": 0.5,
        },
        "strategy": {"allowed_symbols": ["SOXSBUSDT"], "quote_amount_usdt": 77},
        "orders": {"require_stop_loss": True},
        "earn": {"max_redeem_per_run_usdt": "500"},
        "consensus": {"enabled": True},
    }
    config.update(overrides)
    return config


def test_the_seed_divides_by_the_candles_that_exist() -> None:
    closes = [Decimal("52.9")] * 19 + [Decimal("46.70")]

    ema50 = _client()._ema(closes, 50)
    ema200 = _client()._ema(closes, 200)

    # The old seed made these differ by a factor of four; both are now the mean
    # of the twenty candles that exist, so neither invents a level.
    assert ema50 == ema200
    assert Decimal("52") < ema200 < Decimal("53")


def test_a_short_series_never_puts_price_above_its_long_average() -> None:
    """The exact shape of the bug: 46.70 must not sit above a 200-day average."""
    closes = [Decimal("52.9")] * 19 + [Decimal("46.70")]

    assert closes[-1] <= _client()._ema(closes, 200)


def test_ema_still_smooths_once_there_are_more_candles_than_the_period() -> None:
    closes = [Decimal("10")] * 30 + [Decimal("20")] * 30

    ema20 = _client()._ema(closes, 20)

    # Weighted towards the recent half rather than a flat mean of 15.
    assert Decimal("15") < ema20 <= Decimal("20")


def test_short_history_gets_its_own_regime() -> None:
    client = _client()
    closes = [Decimal("50")] * (MIN_TREND_CANDLES - 1)

    regime = client._trend_regime(
        Decimal("50"), Decimal("50"), Decimal("50"), Decimal("50"), Decimal("55"), len(closes)
    )

    assert regime == TREND_INSUFFICIENT_HISTORY


def test_full_history_still_reaches_the_ordinary_regimes() -> None:
    client = _client()

    regime = client._trend_regime(
        Decimal("60"), Decimal("58"), Decimal("55"), Decimal("50"), Decimal("55"), MIN_TREND_CANDLES
    )

    assert regime == "RISK_ON"


def test_risk_engine_refuses_a_buy_on_a_pair_without_history() -> None:
    engine = RiskEngine(_config())

    decision = engine.evaluate(
        _proposal(),
        _state(),
        [_snapshot(TREND_INSUFFICIENT_HISTORY)],
        portfolio_value=Decimal("1000"),
        spendable_quote=Decimal("1000"),
    )

    assert decision.approved is False
    assert "SOXSBUSDT" in decision.reason


def test_the_history_gate_survives_consensus_being_switched_off() -> None:
    """It is the absence of data, not an opinion about the market."""
    engine = RiskEngine(_config(consensus={"enabled": False}))

    decision = engine.evaluate(
        _proposal(),
        _state(),
        [_snapshot(TREND_INSUFFICIENT_HISTORY)],
        portfolio_value=Decimal("1000"),
        spendable_quote=Decimal("1000"),
    )

    assert decision.approved is False


def test_the_history_gate_survives_skip_consensus() -> None:
    engine = RiskEngine(_config())

    decision = engine.evaluate(
        _proposal(),
        _state(),
        [_snapshot(TREND_INSUFFICIENT_HISTORY)],
        skip_consensus=True,
        portfolio_value=Decimal("1000"),
        spendable_quote=Decimal("1000"),
    )

    assert decision.approved is False


def test_a_pair_with_history_is_still_allowed_through() -> None:
    engine = RiskEngine(_config())

    decision = engine.evaluate(
        _proposal(),
        _state(),
        [_snapshot("RISK_ON", price="60", ema200="50")],
        portfolio_value=Decimal("1000"),
        spendable_quote=Decimal("1000"),
    )

    assert decision.approved is True
