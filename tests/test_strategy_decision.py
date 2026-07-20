from decimal import Decimal

from trading_agent.models import GridRecommendation, RiskDecision, TradeProposal
from trading_agent.strategy_decision import StrategyDecisionEngine


def _proposal() -> TradeProposal:
    return TradeProposal(
        symbol="BTCUSDC",
        action="BUY",
        confidence=Decimal("0.7"),
        quote_amount_usdt=Decimal("25"),
        stop_loss_pct=Decimal("0.05"),
        take_profit_pct=Decimal("0.08"),
        reason="test",
    )


def _grid(recommended: bool) -> GridRecommendation:
    return GridRecommendation(
        recommended=recommended,
        market_status="SUITABLE" if recommended else "REJECTED",
        deployment_allowed=recommended,
        symbol="BTCUSDC" if recommended else None,
        reason="test",
        score=Decimal("1"),
        range_low=Decimal("40000"),
        range_high=Decimal("60000"),
        range_width_pct=Decimal("20"),
        grid_count=10,
        grid_type="ARITHMETIC",
        estimated_quote_per_grid=Decimal("2.5"),
        estimated_grid_spacing_pct=Decimal("2"),
        investment_usdt=Decimal("25"),
        stop_loss_price=Decimal("38000"),
        take_profit_price=Decimal("62000"),
        blockers=(),
        candidate_assessments=(),
        manual_steps=(),
    )


def test_grid_recommendation_takes_priority_and_still_carries_an_approved_spot_trade():
    decision = StrategyDecisionEngine().decide(
        proposal=_proposal(),
        risk_decision=RiskDecision(approved=True, reason="ok", adjusted_quote_amount_usdt=Decimal("25")),
        grid_recommendation=_grid(recommended=True),
    )

    assert decision.decision_type == "GRID_BOT_RECOMMENDATION"
    assert decision.priority == "MEDIUM"
    assert decision.spot_trade is not None


def test_grid_recommendation_never_attaches_a_risk_rejected_spot_trade():
    # A GRID_BOT_RECOMMENDATION must not smuggle a spot trade the risk engine rejected.
    decision = StrategyDecisionEngine().decide(
        proposal=_proposal(),
        risk_decision=RiskDecision(approved=False, reason="blocked", adjusted_quote_amount_usdt=Decimal("0")),
        grid_recommendation=_grid(recommended=True),
    )

    assert decision.decision_type == "GRID_BOT_RECOMMENDATION"
    assert decision.spot_trade is None


def test_approved_spot_trade_without_grid_is_a_low_priority_recommendation():
    decision = StrategyDecisionEngine().decide(
        proposal=_proposal(),
        risk_decision=RiskDecision(approved=True, reason="ok", adjusted_quote_amount_usdt=Decimal("25")),
        grid_recommendation=_grid(recommended=False),
    )

    assert decision.decision_type == "SPOT_TRADE_RECOMMENDATION"
    assert decision.priority == "LOW"
    assert decision.spot_trade is not None


def test_rejected_risk_and_no_grid_results_in_hold_with_no_spot_trade():
    # This is the core safety routing: if neither the risk engine nor the grid
    # advisor approves anything, the decision must be HOLD with no trade attached.
    decision = StrategyDecisionEngine().decide(
        proposal=_proposal(),
        risk_decision=RiskDecision(approved=False, reason="blocked", adjusted_quote_amount_usdt=Decimal("0")),
        grid_recommendation=_grid(recommended=False),
    )

    assert decision.decision_type == "HOLD"
    assert decision.spot_trade is None
