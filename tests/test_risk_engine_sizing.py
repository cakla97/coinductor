"""How large an approved order may be.

Before this, the amount was `min(proposal, earn.max_redeem_per_run_usdt)` - a
constant, capped by an Earn limit that has nothing to do with trade size, with
the portfolio nowhere in it. The three percentage limits in `[risk]` were
validated on load, written by the wizard, shown in the UI, and read by nothing.

Every entry is a ceiling and the answer is their minimum, which is what makes
the list safe to add to: no limit can enlarge an order.
`test_no_limit_can_ever_enlarge_the_proposal` holds that line.
"""

from decimal import Decimal

import pytest

from trading_agent.models import LiveRiskState, TradeProposal
from trading_agent.risk_engine import RiskEngine

PORTFOLIO = Decimal("1000")


def _config(earn_cap="50", **risk_overrides) -> dict:
    risk = {
        "max_trades_per_day": 5,
        "max_daily_loss_pct": 100,
        "max_weekly_loss_pct": 100,
        "max_position_pct_per_asset": 10,
        "max_total_trading_capital_pct": 20,
        "max_risk_per_trade_pct": 0.25,
        "min_ai_confidence": 0.5,
        "cooldown_after_loss_hours": 0,
        "max_consecutive_losses": 5,
        "kill_switch_enabled": False,
    }
    risk.update(risk_overrides)
    return {
        "risk": risk,
        "strategy": {"allowed_symbols": ["BTCUSDC"], "quote_amount_usdt": 25},
        "orders": {"require_stop_loss": True},
        "earn": {"max_redeem_per_run_usdt": earn_cap},
        "consensus": {"enabled": False},
    }


def _proposal(amount="25", stop_loss_pct="1.5") -> TradeProposal:
    return TradeProposal(
        symbol="BTCUSDC",
        action="BUY",
        confidence=Decimal("1"),
        quote_amount_usdt=Decimal(amount),
        stop_loss_pct=Decimal(stop_loss_pct),
        take_profit_pct=Decimal("3"),
        reason="test",
    )


def _state() -> LiveRiskState:
    return LiveRiskState(
        enabled=True,
        loss_basis_quote=PORTFOLIO,
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


def _decide(config=None, proposal=None, *, portfolio_value, spendable_quote):
    return RiskEngine(config or _config()).evaluate(
        proposal=proposal or _proposal(),
        risk_state=_state(),
        snapshots=[],
        portfolio_value=portfolio_value,
        spendable_quote=spendable_quote,
    )


def test_funding_caps_the_order_when_the_account_cannot_pay_the_rest() -> None:
    """The case a whole week of journal entries was stuck on.

    Sizing that ignores what is spendable produces an amount the account
    cannot fund, which only surfaces later as an order under the exchange
    minimum - by which point the run has nothing useful to say.
    """
    decision = _decide(portfolio_value=PORTFOLIO, spendable_quote=Decimal("11.89"))

    assert decision.approved is True
    assert decision.adjusted_quote_amount_usdt == Decimal("11.89")
    assert decision.binding_limit == "funding"


def test_the_per_asset_percentage_actually_binds() -> None:
    """10% of 1000 is 100, and the proposal asks for 250."""
    decision = _decide(
        _config(earn_cap="100000"),
        _proposal(amount="250"),
        portfolio_value=PORTFOLIO,
        spendable_quote=Decimal("100000"),
    )

    assert decision.adjusted_quote_amount_usdt == Decimal("100")
    assert decision.binding_limit == "position_per_asset"


def test_the_total_trading_capital_percentage_binds_when_it_is_the_tightest() -> None:
    config = _config(earn_cap="100000", max_position_pct_per_asset=90, max_total_trading_capital_pct=5)

    decision = _decide(
        config,
        _proposal(amount="900"),
        portfolio_value=PORTFOLIO,
        spendable_quote=Decimal("100000"),
    )

    assert decision.adjusted_quote_amount_usdt == Decimal("50")
    assert decision.binding_limit == "total_trading_capital"


def test_risk_per_trade_sizes_against_the_stop_loss() -> None:
    """0.25% of 1000 is 2.50 at risk; a 1% stop reaches that at 250."""
    config = _config(earn_cap="100000", max_position_pct_per_asset=100, max_total_trading_capital_pct=100)

    decision = _decide(
        config,
        _proposal(amount="900", stop_loss_pct="1"),
        portfolio_value=PORTFOLIO,
        spendable_quote=Decimal("100000"),
    )

    assert decision.adjusted_quote_amount_usdt == Decimal("250")
    assert decision.binding_limit == "risk_per_trade"


def test_a_tighter_stop_allows_a_larger_position_for_the_same_risk() -> None:
    """The point of risk-based sizing: risk is held constant, size is not."""
    config = _config(earn_cap="100000", max_position_pct_per_asset=100, max_total_trading_capital_pct=100)

    wide = _decide(config, _proposal(amount="900", stop_loss_pct="2"),
                   portfolio_value=PORTFOLIO, spendable_quote=Decimal("100000"))
    tight = _decide(config, _proposal(amount="900", stop_loss_pct="0.5"),
                    portfolio_value=PORTFOLIO, spendable_quote=Decimal("100000"))

    assert tight.adjusted_quote_amount_usdt > wide.adjusted_quote_amount_usdt


def test_no_portfolio_value_leaves_the_old_sizing_untouched() -> None:
    """What the first-portfolio deployment path relies on.

    That path builds a basket the user sized and confirmed; a ceiling meant
    for tactical trades would refuse to deploy it.
    """
    decision = _decide(portfolio_value=None, spendable_quote=None)

    assert decision.adjusted_quote_amount_usdt == Decimal("25")
    assert decision.binding_limit == "proposal"


def test_an_earn_redeem_limit_does_not_cap_trade_size() -> None:
    """It is how much Earn may release, not how large a trade may be.

    It applied even when the money came entirely from Spot and no redeem was
    going to happen. Where it genuinely matters it is already inside
    `spendable_quote`, which is built from the same redeem bounds.
    """
    decision = _decide(
        proposal=_proposal(amount="900"),
        portfolio_value=None,
        spendable_quote=None,
    )

    assert decision.adjusted_quote_amount_usdt == Decimal("900")
    assert decision.binding_limit == "proposal"


def test_the_redeem_limit_still_bounds_what_is_spendable() -> None:
    """Removing it from sizing must not let a run draw more from Earn.

    The limit is enforced where it belongs - in what the account can pay -
    rather than as a second, differently-shaped cap on the order.
    """
    decision = _decide(
        proposal=_proposal(amount="900"),
        portfolio_value=PORTFOLIO,
        spendable_quote=Decimal("12"),
    )

    assert decision.adjusted_quote_amount_usdt == Decimal("12")
    assert decision.binding_limit == "funding"


def test_a_zero_stop_loss_does_not_divide_by_zero() -> None:
    """require_stop_loss off plus no stop: there is no loss to size against."""
    config = _config()
    config["orders"]["require_stop_loss"] = False

    decision = _decide(
        config,
        _proposal(stop_loss_pct="0"),
        portfolio_value=PORTFOLIO,
        spendable_quote=Decimal("100000"),
    )

    assert decision.approved is True
    assert decision.binding_limit != "risk_per_trade"


def test_nothing_spendable_approves_nothing_to_spend() -> None:
    """Zero is a real answer, and downstream refuses it on minNotional."""
    decision = _decide(portfolio_value=PORTFOLIO, spendable_quote=Decimal("0"))

    assert decision.adjusted_quote_amount_usdt == Decimal("0")
    assert decision.binding_limit == "funding"


def test_a_rejected_proposal_names_no_limit() -> None:
    decision = _decide(
        proposal=TradeProposal(
            symbol="BTCUSDC", action="HOLD", confidence=Decimal("1"),
            quote_amount_usdt=Decimal("25"), stop_loss_pct=Decimal("1.5"),
            take_profit_pct=Decimal("3"), reason="hold",
        ),
        portfolio_value=PORTFOLIO,
        spendable_quote=Decimal("100000"),
    )

    assert decision.approved is False
    assert decision.binding_limit == ""


@pytest.mark.parametrize(
    "portfolio_value,spendable",
    [
        (None, None),
        (Decimal("1000"), Decimal("100000")),
        (Decimal("1000000"), Decimal("1000000")),
        (Decimal("0"), Decimal("0")),
    ],
)
def test_no_limit_can_ever_enlarge_the_proposal(portfolio_value, spendable) -> None:
    """The property that makes this list safe to add to.

    Every entry is a ceiling and the answer is their minimum, so whatever is
    passed, the result cannot exceed what the analyst asked for. If a future
    limit is ever written as a floor rather than a ceiling, this fails.

    Note this is deliberately weaker than "never wider than the previous
    release": removing the Earn redeem cap from sizing does widen one case, on
    purpose, because that cap was never a statement about trade size.
    """
    proposal = _proposal(amount="900")

    decision = _decide(
        proposal=proposal, portfolio_value=portfolio_value, spendable_quote=spendable
    )

    assert decision.adjusted_quote_amount_usdt <= proposal.quote_amount_usdt


def test_funding_is_what_stops_an_order_the_account_cannot_pay() -> None:
    """The guard that replaced the Earn cap, stated as its own expectation."""
    decision = _decide(
        proposal=_proposal(amount="900"),
        portfolio_value=Decimal("1000000"),
        spendable_quote=Decimal("40"),
    )

    assert decision.adjusted_quote_amount_usdt == Decimal("40")


def test_trade_size_scales_with_the_portfolio() -> None:
    """The flat amount means something different at 500 than at 50,000.

    3% of 1000 is 30, under the 900 the analyst asked for and under the flat
    ceiling once that is raised out of the way.
    """
    config = _config(max_position_pct_per_asset=100, max_total_trading_capital_pct=100)
    config["strategy"]["quote_amount_usdt"] = 100000
    config["strategy"]["max_trade_pct_of_portfolio"] = 3

    decision = _decide(
        config,
        _proposal(amount="900", stop_loss_pct="0.01"),
        portfolio_value=PORTFOLIO,
        spendable_quote=Decimal("100000"),
    )

    assert decision.adjusted_quote_amount_usdt == Decimal("30")
    assert decision.binding_limit == "trade_size_pct"


def test_the_flat_amount_still_wins_when_it_is_the_smaller_of_the_two() -> None:
    """It is a hard money limit, not a suggestion the percentage overrides."""
    config = _config(max_position_pct_per_asset=100, max_total_trading_capital_pct=100)
    config["strategy"]["max_trade_pct_of_portfolio"] = 50

    decision = _decide(
        config,
        _proposal(amount="20", stop_loss_pct="0.01"),
        portfolio_value=PORTFOLIO,
        spendable_quote=Decimal("100000"),
    )

    assert decision.adjusted_quote_amount_usdt == Decimal("20")


def test_a_config_without_the_percentage_behaves_as_it_did() -> None:
    """Older configs have no such key; it must not silently shrink them."""
    config = _config(max_position_pct_per_asset=100, max_total_trading_capital_pct=100)
    assert "max_trade_pct_of_portfolio" not in config["strategy"]

    decision = _decide(
        config,
        _proposal(amount="20", stop_loss_pct="0.01"),
        portfolio_value=PORTFOLIO,
        spendable_quote=Decimal("100000"),
    )

    assert decision.adjusted_quote_amount_usdt == Decimal("20")
