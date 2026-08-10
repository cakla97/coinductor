"""Moving Earn to Spot without a person present.

This is the first thing in the engine allowed to POST without somebody typing
a phrase for that exact amount, so what it may and may not do is asserted here
rather than left to the shape of the code.

Why it is treated differently from an order: a redemption moves USDC from
Simple Earn Flexible to Spot inside one account. It changes no exposure, can
lose nothing to the market, costs only forgone yield, and subscribing again
reverses it. An order does none of those things, and nothing here touches how
an order is authorised.
"""

from decimal import Decimal

import pytest

from trading_agent.earn_manager import EarnLiquidityManager
from trading_agent.models import LiquidityDecision, TradingBankrollReport
from trading_agent.safety_state import SafetyState


class _Stage:
    def __init__(self, stage: str):
        self.stage = stage

    def load(self) -> SafetyState:
        return SafetyState(stage=self.stage, detail="test")


def _config(auto: bool = True, **runtime) -> dict:
    return {
        "binance": {"api_base_url": "https://api.binance.com"},
        "earn": {
            "allow_flexible_redeem": True,
            "allowed_redeem_assets": ["USDC"],
            "auto_redeem_assets": ["USDC"],
            "max_auto_redeem_usdc_per_run": "50",
            "min_auto_redeem_reserve_usdc": "0",
            "max_redeem_per_run_usdt": "50",
            "min_flexible_reserve_usdt": "0",
            "max_redeem_per_day_usdt": "100",
            "auto_funding_enabled": auto,
            "redeem_type": "FAST",
        },
        "_runtime": runtime,
    }


@pytest.fixture
def manager(monkeypatch):
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_SECRET", "s")

    def build(auto: bool = True, stage: str = "LIVE_ENABLED", **runtime):
        built = EarnLiquidityManager(_config(auto, **runtime))
        built.safety = _Stage(stage)
        monkeypatch.setattr(
            built.client,
            "get_flexible_positions",
            lambda asset: [{"productId": "p1", "canRedeem": True, "totalAmount": "1000"}],
        )
        built.sent = []
        monkeypatch.setattr(
            built.live_client,
            "redeem_flexible_product",
            lambda product_id, amount, redeem_type: built.sent.append((product_id, amount)) or {"ok": True},
        )
        return built

    return build


def _bankroll(needed="20") -> TradingBankrollReport:
    return TradingBankrollReport(
        enabled=True, quote_asset="USDC", initial_seed=Decimal("100"),
        spot_free=Decimal("0"), flexible_amount=Decimal("500"), total_quote=Decimal("500"),
        realized_pnl=Decimal("0"), profit_available=Decimal("0"),
        seed_capital_at_risk=Decimal("100"), required_amount=Decimal(needed),
        preferred_source="FLEXIBLE_EARN_REDEEM_REQUIRED", max_profit_trade_amount=Decimal("0"),
        flexible_draw_needed=Decimal(needed), summary="test",
    )


def _plan(built, needed="20", redeemed_today="0"):
    return built.plan_flexible_redeem(
        LiquidityDecision(True, "ok", "USDC", Decimal(needed)),
        _bankroll(needed),
        existing_intents=set(),
        redeemed_today=Decimal(redeemed_today),
        portfolio_value=Decimal("1000000"),
    )


def test_it_moves_the_money_when_switched_on_and_armed(manager) -> None:
    built = manager()

    plan = _plan(built)

    assert plan.status == "SUBMITTED"
    assert plan.submitted is True
    assert built.sent == [("p1", Decimal("20"))]
    # The journal has to say which authority acted, not just that it happened.
    assert "automatic" in plan.message


def test_it_does_nothing_when_the_switch_is_off(manager) -> None:
    """The default. Absent means off, and off means a preview as before."""
    built = manager(auto=False)

    plan = _plan(built)

    assert plan.status == "PREVIEW_READY"
    assert plan.submitted is False
    assert built.sent == []


@pytest.mark.parametrize("stage", ["SETUP", "READ_ONLY_CONNECTED", "TESTNET_READY", "PREVIEW_ONLY", "ARMED"])
def test_it_refuses_below_live_enabled(manager, stage: str) -> None:
    """The stage is reached by hand, on screen. A setting cannot substitute."""
    built = manager(stage=stage)

    plan = _plan(built)

    assert plan.status == "PREVIEW_READY"
    assert built.sent == []


def test_an_unreadable_safety_stage_is_not_permission(manager) -> None:
    built = manager()

    class _Broken:
        def load(self):
            raise OSError("no state file")

    built.safety = _Broken()

    assert _plan(built).status == "PREVIEW_READY"
    assert built.sent == []


def test_it_needs_no_confirmation_phrase(manager) -> None:
    """The phrase belongs to the manual path and stays there.

    A standing arrangement that also demanded a phrase would be no
    arrangement at all; what bounds this instead is the switch, the stage, and
    the per-run and per-day limits.
    """
    built = manager()
    assert built.runtime.earn_redeem_confirm == ""

    assert _plan(built).status == "SUBMITTED"


def test_the_manual_path_still_demands_its_phrase(manager) -> None:
    """Auto-funding must not become a way around the typed confirmation."""
    built = manager(auto=False, earn_redeem_submit=True)

    plan = _plan(built)

    assert plan.status == "SUBMIT_SKIPPED"
    assert built.sent == []


def test_a_person_typing_the_phrase_still_works(manager) -> None:
    built = manager(auto=False, earn_redeem_submit=True, earn_redeem_confirm="CONFIRM_EARN_REDEEM")

    plan = _plan(built)

    assert plan.status == "SUBMITTED"
    assert "manual" in plan.message


def test_it_stays_inside_the_per_run_limit(manager) -> None:
    built = manager()
    built.config["earn"]["max_auto_redeem_usdc_per_run"] = "8"

    assert _plan(built, needed="20").amount == Decimal("8")
    assert built.sent == [("p1", Decimal("8"))]


def test_it_stays_inside_what_the_day_has_left(manager) -> None:
    built = manager()

    plan = _plan(built, needed="20", redeemed_today="95")

    assert plan.amount == Decimal("5")
    assert built.sent == [("p1", Decimal("5"))]


def test_an_exhausted_day_moves_nothing(manager) -> None:
    built = manager()

    plan = _plan(built, needed="20", redeemed_today="100")

    assert plan.submitted is False
    assert built.sent == []


def test_nothing_moves_when_no_approved_action_needs_it(manager) -> None:
    """Structural: a rejected proposal produces no redeem amount to plan for."""
    built = manager()

    plan = built.plan_flexible_redeem(
        LiquidityDecision(False, "risk rejected", None, Decimal("0")),
        _bankroll(),
        existing_intents=set(),
        redeemed_today=Decimal("0"),
        portfolio_value=Decimal("1000000"),
    )

    assert plan.status == "NOT_NEEDED"
    assert built.sent == []


def test_an_already_submitted_intent_is_not_repeated(manager) -> None:
    """A schedule reruns often; the same draw must not go twice."""
    built = manager()
    first = _plan(built)

    built.sent.clear()
    again = built.plan_flexible_redeem(
        LiquidityDecision(True, "ok", "USDC", Decimal("20")),
        _bankroll(),
        existing_intents={first.intent_id},
        redeemed_today=Decimal("0"),
        portfolio_value=Decimal("1000000"),
    )

    assert again.status == "BLOCKED"
    assert built.sent == []
