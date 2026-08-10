from decimal import Decimal

from trading_agent.earn_manager import EarnLiquidityManager
from trading_agent.models import Balance, LiquidityDecision, TradingBankrollReport
from trading_agent.order_journal import OrderIntentFactory


def _config(**runtime) -> dict:
    return {
        "binance": {"api_base_url": "https://api.binance.com"},
        "earn": {
            "allow_flexible_redeem": True,
            "allowed_redeem_assets": ["USDC"],
            "auto_redeem_assets": ["USDC"],
            "max_auto_redeem_usdc_per_run": "50",
            "min_auto_redeem_reserve_usdc": "10",
            "redeem_type": "FAST",
        },
        "_runtime": runtime,
    }


def _bankroll() -> TradingBankrollReport:
    return TradingBankrollReport(
        enabled=True,
        quote_asset="USDC",
        initial_seed=Decimal("100"),
        spot_free=Decimal("0"),
        flexible_amount=Decimal("250"),
        total_quote=Decimal("250"),
        realized_pnl=Decimal("0"),
        profit_available=Decimal("0"),
        seed_capital_at_risk=Decimal("100"),
        required_amount=Decimal("30"),
        preferred_source="FLEXIBLE_EARN_REDEEM_REQUIRED",
        max_profit_trade_amount=Decimal("0"),
        flexible_draw_needed=Decimal("30"),
        summary="test bankroll",
    )


def _manager(monkeypatch, **runtime) -> EarnLiquidityManager:
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_KEY", "live-key")
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_SECRET", "live-secret")
    return EarnLiquidityManager(_config(**runtime))


def test_earn_redeem_intent_id_is_pure_and_deterministic():
    factory = OrderIntentFactory({"paper": {"idempotency_window": "daily"}})

    first = factory.earn_redeem_intent_id("USDC", Decimal("30.00"))
    second = factory.earn_redeem_intent_id("USDC", Decimal("30.00"))

    assert first == second
    assert factory.earn_redeem_intent_id("USDT", Decimal("30.00")) != first
    assert factory.earn_redeem_intent_id("USDC", Decimal("31.00")) != first


def test_repeated_redeem_plan_blocks_on_already_submitted_intent(monkeypatch):
    # Regression test: without an idempotency check, a run that starts before the
    # previous run's redeem is confirmed on Binance could plan (and, if submit is
    # requested, actually redeem) the same amount twice.
    manager = _manager(monkeypatch)
    monkeypatch.setattr(
        manager.client,
        "get_flexible_positions",
        lambda asset: [{"productId": "prod-1", "canRedeem": True, "totalAmount": "1000"}],
    )
    liquidity = LiquidityDecision(True, "ok", "USDC", Decimal("30"))
    bankroll = _bankroll()

    first = manager.plan_flexible_redeem(liquidity, bankroll, existing_intents=set(), redeemed_today=Decimal("0"), portfolio_value=Decimal("1000000"))
    assert first.status == "PREVIEW_READY"
    assert first.intent_id

    def fail_if_called(asset):
        raise AssertionError("must not query Binance again for an already-submitted redeem intent")

    monkeypatch.setattr(manager.client, "get_flexible_positions", fail_if_called)

    second = manager.plan_flexible_redeem(
        liquidity, bankroll, existing_intents={first.intent_id}, redeemed_today=Decimal("0"), portfolio_value=Decimal("1000000")
    )

    assert second.status == "BLOCKED"
    assert second.intent_id == first.intent_id
    assert "already submitted" in second.message


def _spendable_config(**earn) -> dict:
    settings = {
        "allow_flexible_redeem": True,
        "allowed_redeem_assets": ["USDC"],
        "auto_redeem_assets": ["USDC"],
        "max_auto_redeem_usdc_per_run": "12",
        "min_auto_redeem_reserve_usdc": "0",
        "max_redeem_per_run_usdt": "50",
        "min_flexible_reserve_usdt": "25",
    }
    settings.update(earn)
    return {"binance": {"api_base_url": "https://api.binance.com"}, "earn": settings, "_runtime": {}}


def _balances(spot="0", flexible="0") -> list[Balance]:
    return [Balance(asset="USDC", spot_free=Decimal(spot), flexible_amount=Decimal(flexible))]


def test_spendable_is_spot_plus_what_this_run_may_redeem(monkeypatch) -> None:
    """What the risk engine sizes against, so it cannot approve the unpayable."""
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_SECRET", "s")
    manager = EarnLiquidityManager(_spendable_config())

    # 5 free, 11.89 in Earn, per-run cap 12, no reserve for an auto asset.
    assert manager.spendable_quote(_balances("5", "11.89"), "USDC", redeemed_today=Decimal("0"), portfolio_value=Decimal("1000000")) == Decimal("16.89")


def test_the_per_run_cap_limits_what_counts_as_spendable(monkeypatch) -> None:
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_SECRET", "s")
    manager = EarnLiquidityManager(_spendable_config())

    assert manager.spendable_quote(_balances("0", "500"), "USDC", redeemed_today=Decimal("0"), portfolio_value=Decimal("1000000")) == Decimal("12")


def test_a_non_auto_asset_uses_the_manual_reserve(monkeypatch) -> None:
    """25 reserve, 50 per run: 30 in Earn leaves 5 reachable."""
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_SECRET", "s")
    manager = EarnLiquidityManager(_spendable_config(auto_redeem_assets=[]))

    assert manager.spendable_quote(_balances("0", "30"), "USDC", redeemed_today=Decimal("0"), portfolio_value=Decimal("1000000")) == Decimal("5")


def test_redeem_disabled_leaves_only_the_spot_balance(monkeypatch) -> None:
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_SECRET", "s")
    manager = EarnLiquidityManager(_spendable_config(allow_flexible_redeem=False))

    assert manager.spendable_quote(_balances("7", "500"), "USDC", redeemed_today=Decimal("0"), portfolio_value=Decimal("1000000")) == Decimal("7")


def test_an_asset_outside_the_allowed_list_cannot_be_drawn(monkeypatch) -> None:
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_SECRET", "s")
    manager = EarnLiquidityManager(_spendable_config(allowed_redeem_assets=["BUSD"]))

    assert manager.spendable_quote(_balances("3", "500"), "USDC", redeemed_today=Decimal("0"), portfolio_value=Decimal("1000000")) == Decimal("3")
