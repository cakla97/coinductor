from decimal import Decimal

from trading_agent.grid_advisor import GridBotAdvisor
from trading_agent.models import (
    ActiveStrategiesReport,
    LiveRiskState,
    MarketBreadth,
    MarketResearchReport,
    MarketSnapshot,
    SymbolMarketResearch,
)


def _config() -> dict:
    return {
        "grid_bot": {
            "enabled": True,
            "allowed_symbols": ["BTCUSDC", "ETHUSDC"],
            "preferred_symbols": ["BTCUSDC", "ETHUSDC"],
            "max_active_grid_bots": 1,
            "max_grid_capital_usdt": 50,
            "max_grid_capital_pct": 7.5,
            "default_investment_usdt": 25,
            "min_range_width_pct": 5,
            "max_range_width_pct": 25,
            "min_grid_count": 8,
            "max_grid_count": 40,
            "preferred_grid_count": 20,
            "min_quote_per_grid_usdt": 2.5,
            "target_rsi14": 52,
            "min_rsi14": 40,
            "max_rsi14": 65,
            "min_atr_pct": 1,
            "max_atr_pct": 6,
            "max_abs_ema200_distance_pct": 12,
            "max_abs_7d_return_pct": 10,
            "suitable_score": 70,
            "watch_score": 45,
            "atr_range_multiplier": 4,
            "stop_loss_buffer_pct": 3,
            "take_profit_buffer_pct": 3,
        }
    }


def _snapshot(symbol: str, regime: str = "NEUTRAL", price: str = "100") -> MarketSnapshot:
    value = Decimal(price)
    return MarketSnapshot(
        symbol=symbol,
        price=value,
        ema20=value * Decimal("1.02"),
        ema50=value * Decimal("0.98"),
        ema200=value * Decimal("0.96"),
        rsi14=Decimal("52"),
        atr14=value * Decimal("0.025"),
        volume_trend="rising",
        trend_regime=regime,
    )


def _research(symbol: str, return_7d: str = "2") -> SymbolMarketResearch:
    return SymbolMarketResearch(
        symbol=symbol,
        change_24h_pct=Decimal("0.5"),
        return_7d_pct=Decimal(return_7d),
        return_30d_pct=Decimal("3"),
        quote_volume_24h=Decimal("100000000"),
        trades_24h=100000,
        range_24h_pct=Decimal("4"),
        atr_pct=Decimal("2.5"),
        price_vs_ema200_pct=Decimal("4"),
        relative_strength_vs_btc_24h_pct=Decimal("0"),
        support_30d=Decimal("92"),
        resistance_30d=Decimal("108"),
        volume_trend="rising",
        trend_regime="NEUTRAL",
    )


def _research_report(items: tuple[SymbolMarketResearch, ...]) -> MarketResearchReport:
    breadth = MarketBreadth("USDC", 50, 25, 25, 0, Decimal("50"), Decimal("0"), (), (), ())
    return MarketResearchReport(True, "OK", items, breadth, (), "test")


def _risk_state(blocked: bool = False) -> LiveRiskState:
    return LiveRiskState(
        enabled=True,
        loss_basis_quote=Decimal("12"),
        trades_today=0,
        daily_realized_pnl_quote=Decimal("0"),
        weekly_realized_pnl_quote=Decimal("0"),
        daily_loss_pct=Decimal("0"),
        weekly_loss_pct=Decimal("0"),
        consecutive_losses=0,
        last_loss_at=None,
        hours_since_last_loss=None,
        cooldown_active=blocked,
        daily_limit_reached=blocked,
        weekly_limit_reached=False,
        consecutive_loss_limit_reached=False,
        kill_switch_active=blocked,
        summary="blocked" if blocked else "clear",
    )


def test_selects_best_range_candidate_and_caps_grid_count_by_capital() -> None:
    advisor = GridBotAdvisor(_config())
    btc = _snapshot("BTCUSDC")
    eth = _snapshot("ETHUSDC", regime="RISK_ON")
    report = _research_report((_research("BTCUSDC"), _research("ETHUSDC", "9")))

    recommendation = advisor.recommend(
        [btc, eth],
        report,
        ActiveStrategiesReport(True, (), "none"),
        _risk_state(),
        Decimal("800"),
    )

    assert recommendation.symbol == "BTCUSDC"
    assert recommendation.market_status == "SUITABLE"
    assert recommendation.deployment_allowed is True
    assert recommendation.recommended is True
    assert recommendation.grid_count == 10
    assert recommendation.estimated_quote_per_grid == Decimal("2.50")
    assert recommendation.range_low < btc.price < recommendation.range_high
    assert [item.symbol for item in recommendation.candidate_assessments] == ["BTCUSDC", "ETHUSDC"]


def test_suitable_grid_is_blocked_by_live_risk_state() -> None:
    advisor = GridBotAdvisor(_config())
    recommendation = advisor.recommend(
        [_snapshot("BTCUSDC")],
        _research_report((_research("BTCUSDC"),)),
        ActiveStrategiesReport(True, (), "none"),
        _risk_state(blocked=True),
        Decimal("800"),
    )

    assert recommendation.market_status == "SUITABLE"
    assert recommendation.deployment_allowed is False
    assert recommendation.recommended is False
    assert "live risk kill switch is active" in recommendation.blockers
    assert "loss cooldown is active" in recommendation.blockers


def test_risk_off_market_is_not_recommended() -> None:
    advisor = GridBotAdvisor(_config())
    recommendation = advisor.recommend(
        [_snapshot("BTCUSDC", regime="RISK_OFF")],
        _research_report((_research("BTCUSDC", "-12"),)),
        ActiveStrategiesReport(True, (), "none"),
        _risk_state(),
        Decimal("800"),
    )

    assert recommendation.market_status != "SUITABLE"
    assert recommendation.recommended is False
    assert recommendation.blockers
