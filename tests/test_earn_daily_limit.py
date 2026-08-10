"""`earn.max_redeem_per_day_usdt` bounds a day's Flexible Earn draw.

It used to be read by nothing at all: the validator required it to be
positive and no code ever compared anything to it, so a number that reads like
a daily guarantee guaranteed nothing. Only the per-run cap existed, which on a
schedule running every two hours is twelve times weaker than it looks.
"""

from decimal import Decimal

import pytest

from trading_agent.earn_manager import EarnLiquidityManager
from trading_agent.models import Balance, LiquidityDecision, TradingBankrollReport
from trading_agent.storage import Storage


def _config(**earn) -> dict:
    settings = {
        "allow_flexible_redeem": True,
        "allowed_redeem_assets": ["USDC"],
        "auto_redeem_assets": ["USDC"],
        "max_auto_redeem_usdc_per_run": "12",
        "min_auto_redeem_reserve_usdc": "0",
        "max_redeem_per_run_usdt": "50",
        "min_flexible_reserve_usdt": "25",
        "max_redeem_per_day_usdt": "30",
    }
    settings.update(earn)
    return {"binance": {"api_base_url": "https://api.binance.com"}, "earn": settings, "_runtime": {}}


@pytest.fixture
def manager(monkeypatch):
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_SECRET", "s")

    def build(**earn):
        return EarnLiquidityManager(_config(**earn))

    return build


def _balances(spot="0", flexible="500") -> list[Balance]:
    return [Balance(asset="USDC", spot_free=Decimal(spot), flexible_amount=Decimal(flexible))]


def test_the_day_still_has_room(manager) -> None:
    """24 spent of 30 leaves 6, below the per-run 12."""
    assert manager().spendable_quote(
        _balances(), "USDC", redeemed_today=Decimal("24")
    ) == Decimal("6")


def test_an_exhausted_day_reaches_nothing(manager) -> None:
    assert manager().spendable_quote(
        _balances(), "USDC", redeemed_today=Decimal("30")
    ) == Decimal("0")


def test_overshooting_the_day_does_not_go_negative(manager) -> None:
    """A cap lowered after the fact must not produce a negative allowance."""
    assert manager().spendable_quote(
        _balances(), "USDC", redeemed_today=Decimal("100")
    ) == Decimal("0")


def test_the_per_run_cap_still_binds_when_it_is_tighter(manager) -> None:
    """Nothing spent today, so the per-run 12 decides rather than the daily 30."""
    assert manager().spendable_quote(
        _balances(), "USDC", redeemed_today=Decimal("0")
    ) == Decimal("12")


def test_spot_is_untouched_by_the_daily_cap(manager) -> None:
    """The limit is on releasing Earn, not on spending money already in Spot."""
    assert manager().spendable_quote(
        _balances(spot="40"), "USDC", redeemed_today=Decimal("30")
    ) == Decimal("40")


def test_no_daily_cap_configured_means_no_daily_limit(manager) -> None:
    """How every config written before this behaved; absence must not shrink them."""
    built = manager()
    del built.config["earn"]["max_redeem_per_day_usdt"]

    assert built.spendable_quote(
        _balances(), "USDC", redeemed_today=Decimal("9999")
    ) == Decimal("12")


def test_the_liquidity_check_respects_the_day(manager) -> None:
    decision = manager().ensure_quote_liquidity(
        _balances(), "USDC", Decimal("25"), redeemed_today=Decimal("28")
    )

    assert decision.redeem_amount == Decimal("2")
    # 2 released against 25 needed is not enough, and it says so rather than
    # letting the order proceed towards a balance that cannot cover it.
    assert decision.approved is False


def test_the_submitted_plan_cannot_exceed_the_day(manager, monkeypatch) -> None:
    built = manager()
    monkeypatch.setattr(
        built.client,
        "get_flexible_positions",
        lambda asset: [{"productId": "p1", "canRedeem": True, "totalAmount": "1000"}],
    )
    bankroll = TradingBankrollReport(
        enabled=True, quote_asset="USDC", initial_seed=Decimal("100"),
        spot_free=Decimal("0"), flexible_amount=Decimal("500"), total_quote=Decimal("500"),
        realized_pnl=Decimal("0"), profit_available=Decimal("0"),
        seed_capital_at_risk=Decimal("100"), required_amount=Decimal("12"),
        preferred_source="FLEXIBLE_EARN_REDEEM_REQUIRED", max_profit_trade_amount=Decimal("0"),
        flexible_draw_needed=Decimal("12"), summary="test",
    )

    plan = built.plan_flexible_redeem(
        LiquidityDecision(True, "ok", "USDC", Decimal("12")),
        bankroll,
        existing_intents=set(),
        redeemed_today=Decimal("25"),
    )

    assert plan.amount == Decimal("5")


# ---------------------------------------------------------------------------
# The day's total, out of the journal.
# ---------------------------------------------------------------------------


def _save(storage: Storage, run_id: int, amount: str, *, submitted: bool, status: str = "SUBMITTED") -> None:
    storage.connection.execute(
        "insert into earn_redeem_plans (run_id, intent_id, amount, submitted, status) values (?, ?, ?, ?, ?)",
        (run_id, f"i{run_id}", amount, int(submitted), status),
    )
    storage.connection.commit()


def test_the_days_total_adds_up_submitted_redeems(tmp_path) -> None:
    storage = Storage(tmp_path / "j.sqlite3")
    first, second, current = storage.start_run("DRY_RUN"), storage.start_run("DRY_RUN"), storage.start_run("DRY_RUN")
    _save(storage, first, "7.5", submitted=True)
    _save(storage, second, "4.25", submitted=True)

    assert storage.get_earn_redeemed_today(current) == Decimal("11.75")


def test_an_unconfirmed_plan_does_not_spend_the_day(tmp_path) -> None:
    """It moved no money; counting it would let a preview exhaust the allowance."""
    storage = Storage(tmp_path / "j.sqlite3")
    planned, current = storage.start_run("DRY_RUN"), storage.start_run("DRY_RUN")
    _save(storage, planned, "12", submitted=False, status="PREVIEW_READY")

    assert storage.get_earn_redeemed_today(current) == Decimal("0")


def test_a_failed_submission_does_not_spend_the_day(tmp_path) -> None:
    storage = Storage(tmp_path / "j.sqlite3")
    failed, current = storage.start_run("DRY_RUN"), storage.start_run("DRY_RUN")
    _save(storage, failed, "12", submitted=True, status="SUBMIT_ERROR")

    assert storage.get_earn_redeemed_today(current) == Decimal("0")


def test_yesterdays_redeems_do_not_count(tmp_path) -> None:
    storage = Storage(tmp_path / "j.sqlite3")
    yesterday, current = storage.start_run("DRY_RUN"), storage.start_run("DRY_RUN")
    storage.connection.execute(
        "update runs set started_at = datetime(started_at, '-1 day') where id = ?", (yesterday,)
    )
    _save(storage, yesterday, "30", submitted=True)

    assert storage.get_earn_redeemed_today(current) == Decimal("0")


def test_an_empty_journal_has_spent_nothing(tmp_path) -> None:
    storage = Storage(tmp_path / "j.sqlite3")

    assert storage.get_earn_redeemed_today(storage.start_run("DRY_RUN")) == Decimal("0")
