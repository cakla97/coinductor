"""A standing authorisation: permission to submit with nobody in the room.

Written before the implementation, deliberately. This is the only thing in
Coinductor that can put an order on a real exchange without a person present,
so the tests are the specification and the feature does not ship unless they
pass.

The default answer everywhere is no. Every test below that expects `allowed`
had to satisfy all of: an unexpired, unrevoked grant, the right symbol, the
right side, an amount inside the per-order cap, a running total inside the
window cap, and a safety stage of LIVE_ENABLED. Any one of them missing is a
refusal, and each refusal names itself so the journal can say which gate said
no.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from coinductor.standing_authorisation import (
    MAX_WINDOW_DAYS,
    StandingAuthorisationStore,
    evaluate,
)

NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(days=3)
AFTER_EXPIRY = NOW + timedelta(days=8)


def _store(tmp_path: Path) -> StandingAuthorisationStore:
    return StandingAuthorisationStore(tmp_path / "standing_authorisation.toml")


def _grant(store: StandingAuthorisationStore, **overrides):
    defaults = {
        "symbol": "BTCUSDC",
        "side": "BUY",
        "per_order_cap": Decimal("50"),
        "window_cap": Decimal("150"),
        "days": 7,
        "now": NOW,
    }
    return store.grant(**{**defaults, **overrides})


def _decide(store, *, symbol="BTCUSDC", side="BUY", amount="40", now=LATER, stage="LIVE_ENABLED"):
    # stored(), not current(): the gate wants to see an expired authorisation so
    # it can say "expired" rather than "none". current() is for the screen.
    return evaluate(
        store.stored(),
        symbol=symbol,
        side=side,
        amount=Decimal(amount),
        now=now,
        safety_stage=stage,
    )


# --- the default is no ------------------------------------------------------


def test_with_no_authorisation_nothing_is_allowed(tmp_path) -> None:
    """The state every install starts in and returns to when one expires."""
    decision = _decide(_store(tmp_path))

    assert decision.allowed is False
    assert decision.reason == "standing_none"


def test_a_corrupt_file_refuses_rather_than_defaulting_to_permitted(tmp_path) -> None:
    path = tmp_path / "standing_authorisation.toml"
    path.write_text("not toml [[[", encoding="utf-8")

    decision = _decide(StandingAuthorisationStore(path))

    assert decision.allowed is False
    assert decision.reason == "standing_none"


# --- what a valid one permits ----------------------------------------------


def test_everything_satisfied_is_allowed(tmp_path) -> None:
    store = _store(tmp_path)
    _grant(store)

    decision = _decide(store)

    assert decision.allowed is True
    assert decision.reason == "standing_allowed"


def test_an_order_exactly_on_the_per_order_cap_is_allowed(tmp_path) -> None:
    store = _store(tmp_path)
    _grant(store)

    assert _decide(store, amount="50").allowed is True


# --- every gate, one at a time ---------------------------------------------


def test_an_expired_authorisation_refuses(tmp_path) -> None:
    """A permission with no end is one nobody remembers granting."""
    store = _store(tmp_path)
    _grant(store)

    decision = _decide(store, now=AFTER_EXPIRY)

    assert decision.allowed is False
    assert decision.reason == "standing_expired"


def test_a_revoked_authorisation_refuses_immediately(tmp_path) -> None:
    store = _store(tmp_path)
    _grant(store)

    store.revoke()

    assert _decide(store).allowed is False
    assert _decide(store).reason == "standing_none"


def test_a_different_symbol_refuses(tmp_path) -> None:
    """"You may buy BTCUSDC" is checkable; "you may trade" is not."""
    store = _store(tmp_path)
    _grant(store)

    decision = _decide(store, symbol="ETHUSDC")

    assert decision.allowed is False
    assert decision.reason == "standing_other_symbol"


def test_selling_refuses_even_on_the_authorised_symbol(tmp_path) -> None:
    store = _store(tmp_path)
    _grant(store)

    decision = _decide(store, side="SELL")

    assert decision.allowed is False
    assert decision.reason == "standing_other_side"


def test_an_order_over_the_per_order_cap_refuses_rather_than_shrinking(tmp_path) -> None:
    """Unlike the display-time cap, this refuses.

    Truncating an order nobody is watching turns "I authorised 50" into a
    stream of 50s, which is the opposite of what a cap is for.
    """
    store = _store(tmp_path)
    _grant(store)

    decision = _decide(store, amount="50.01")

    assert decision.allowed is False
    assert decision.reason == "standing_over_order_cap"


def test_a_safety_stage_below_live_enabled_refuses(tmp_path) -> None:
    store = _store(tmp_path)
    _grant(store)

    for stage in ("PREVIEW_ONLY", "ARMED", "", "live_enabled_but_not_really"):
        decision = _decide(store, stage=stage)
        assert decision.allowed is False, f"{stage} was accepted"
        assert decision.reason == "standing_stage"


# --- the window cap, which is what makes the per-order cap mean anything ----


def test_spending_accumulates_and_the_window_cap_refuses(tmp_path) -> None:
    """A per-order cap alone permits an unlimited number of orders."""
    store = _store(tmp_path)
    _grant(store)

    for _ in range(3):
        assert _decide(store, amount="50").allowed is True
        store.record_use(Decimal("50"), now=LATER)

    decision = _decide(store, amount="50")

    assert decision.allowed is False
    assert decision.reason == "standing_over_window_cap"


def test_a_partial_spend_leaves_only_the_remainder(tmp_path) -> None:
    store = _store(tmp_path)
    _grant(store)
    store.record_use(Decimal("120"), now=LATER)

    assert _decide(store, amount="30").allowed is True
    assert _decide(store, amount="31").reason == "standing_over_window_cap"


def test_use_survives_a_restart(tmp_path) -> None:
    """Spending held only in memory would reset every time the app reopened."""
    store = _store(tmp_path)
    _grant(store)
    store.record_use(Decimal("150"), now=LATER)

    assert _decide(_store(tmp_path), amount="1").reason == "standing_over_window_cap"


def test_recording_a_use_without_an_authorisation_does_nothing(tmp_path) -> None:
    store = _store(tmp_path)

    store.record_use(Decimal("50"), now=LATER)

    assert store.current(now=LATER) is None


# --- granting is itself bounded --------------------------------------------


def test_a_window_longer_than_the_maximum_is_refused(tmp_path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError):
        _grant(store, days=MAX_WINDOW_DAYS + 1)

    assert store.current(now=NOW) is None


def test_a_non_positive_cap_is_refused(tmp_path) -> None:
    store = _store(tmp_path)

    for bad in (Decimal("0"), Decimal("-1")):
        with pytest.raises(ValueError):
            _grant(store, per_order_cap=bad)
        with pytest.raises(ValueError):
            _grant(store, window_cap=bad)

    assert store.current(now=NOW) is None


def test_a_per_order_cap_above_the_window_cap_is_refused(tmp_path) -> None:
    """It would read as a limit while permitting the whole window in one go."""
    store = _store(tmp_path)

    with pytest.raises(ValueError):
        _grant(store, per_order_cap=Decimal("200"), window_cap=Decimal("150"))


def test_only_buying_can_be_authorised(tmp_path) -> None:
    """Selling is how someone exits; it should not need standing permission."""
    store = _store(tmp_path)

    with pytest.raises(ValueError):
        _grant(store, side="SELL")


def test_granting_replaces_rather_than_stacking(tmp_path) -> None:
    """Two live authorisations would make the window cap meaningless."""
    store = _store(tmp_path)
    _grant(store, symbol="BTCUSDC")

    _grant(store, symbol="ETHUSDC")

    assert _decide(store, symbol="BTCUSDC").reason == "standing_other_symbol"
    assert _decide(store, symbol="ETHUSDC").allowed is True


def test_a_new_grant_resets_the_spend(tmp_path) -> None:
    store = _store(tmp_path)
    _grant(store)
    store.record_use(Decimal("150"), now=LATER)

    _grant(store, now=LATER)

    assert _decide(store, amount="50", now=LATER).allowed is True


# --- describing itself, because a permission nobody can see is not one ------


def test_a_live_authorisation_describes_what_it_permits(tmp_path) -> None:
    store = _store(tmp_path)
    _grant(store)
    store.record_use(Decimal("40"), now=LATER)

    live = store.current(now=LATER)

    assert live is not None
    assert live.symbol == "BTCUSDC"
    assert live.side == "BUY"
    assert live.per_order_cap == Decimal("50")
    assert live.window_cap == Decimal("150")
    assert live.spent == Decimal("40")
    assert live.remaining == Decimal("110")
    assert live.expires_at > LATER


def test_an_expired_one_is_not_returned_as_current(tmp_path) -> None:
    store = _store(tmp_path)
    _grant(store)

    assert store.current(now=AFTER_EXPIRY) is None
