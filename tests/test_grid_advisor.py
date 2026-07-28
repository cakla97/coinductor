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
    assert recommendation.range_low < btc.price < recommendation.range_high
    assert [item.symbol for item in recommendation.candidate_assessments] == ["BTCUSDC", "ETHUSDC"]
    # The shipped defaults cannot fund a grid Binance would accept - see
    # test_shipped_defaults_cannot_fund_a_grid_binance_would_accept.
    assert recommendation.deployment_allowed is False


def test_shipped_defaults_cannot_fund_a_grid_binance_would_accept() -> None:
    """The recommendation was a recipe that dead-ends at the exchange.

    Binance's NOTIONAL filter rejects any order under 5 USDC, so a grid funded
    at 2.50 per level cannot place one - yet the advisor recommended it, handed
    over the parameters, and the user only found out when Binance quoted its own
    minimum. The floor is the exchange's, not a preference, so it applies even
    to a config written before this check existed.
    """
    advisor = GridBotAdvisor(_config())

    recommendation = advisor.recommend(
        [_snapshot("BTCUSDC"), _snapshot("ETHUSDC", regime="RISK_ON")],
        _research_report((_research("BTCUSDC"), _research("ETHUSDC", "9"))),
        ActiveStrategiesReport(True, (), "none"),
        _risk_state(),
        Decimal("800"),
    )

    assert recommendation.deployment_allowed is False
    assert recommendation.recommended is False
    blocker = next(item for item in recommendation.blockers if "not enough grid capital" in item)
    assert blocker == "not enough grid capital: 8 grids need 40.00 USDC, only 25.00 is allocated"
    # This line is repeated on the card, in the blockers field and in the
    # next-review panel, so length is paid for three times.
    assert len(blocker) < 100, f"blocker is a paragraph again: {len(blocker)} chars"
    assert "config" not in blocker, "config keys belong in the steps, not in a skimmed line"
    # And it is not inlined into the reason as well.
    assert "not enough grid capital" not in recommendation.reason
    assert len(recommendation.reason) < 200, "the reason grew back into a wall of text"
    # The steps say the grid is out of reach at this budget. They do not send a
    # desktop user into a config file to change how much of their own money the
    # app may commit - there is no control for that in the app yet.
    assert any("more capital than your current budget" in step for step in recommendation.manual_steps)
    assert not any("config.toml" in step for step in recommendation.manual_steps)
    assert not any("default_investment_usdt" in step for step in recommendation.manual_steps)
    # Blocked grids still drop their parameters: the range is derived from
    # today's prices and would be stale by the time the capital is raised.
    assert not any("Investment currency dropdown" in step for step in recommendation.manual_steps)


def test_a_properly_funded_grid_still_deploys() -> None:
    config = _config()
    config["grid_bot"]["default_investment_usdt"] = 120
    config["grid_bot"]["max_grid_capital_usdt"] = 200
    advisor = GridBotAdvisor(config)

    recommendation = advisor.recommend(
        [_snapshot("BTCUSDC"), _snapshot("ETHUSDC", regime="RISK_ON")],
        _research_report((_research("BTCUSDC"), _research("ETHUSDC", "9"))),
        ActiveStrategiesReport(True, (), "none"),
        _risk_state(),
        Decimal("4000"),
    )

    assert recommendation.deployment_allowed is True
    assert recommendation.recommended is True
    assert recommendation.estimated_quote_per_grid >= Decimal("5")
    assert any("Investment currency dropdown select USDC" in step for step in recommendation.manual_steps)
    assert any("Trading Up OFF" in step for step in recommendation.manual_steps)
    assert any("Enable TP/SL" in step for step in recommendation.manual_steps)


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
