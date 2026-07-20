from decimal import Decimal

from trading_agent.capital_sourcing import CapitalSourcingAdvisor
from trading_agent.models import Balance, PortfolioAnalysis, PortfolioAssetValuation


def _config(**overrides) -> dict:
    capital_sourcing = {
        "enabled": True,
        "max_source_value_usdt_per_run": "20",
        "max_source_pct_per_asset": "15",
        "max_total_source_pct_per_run": "10",
        "min_remaining_value_usdt_per_asset": "50",
        "min_remaining_pct_per_asset": "70",
        "allowed_source_assets": ["SOL", "WLD"],
        "protected_assets": ["BTC", "ETH"],
    }
    capital_sourcing.update(overrides)
    return {"capital_sourcing": capital_sourcing, "live_confirm": {"quote_asset": "USDC"}}


def _asset(asset: str, total_value_usdt: Decimal, rebalance_action: str = "NO_TARGET") -> PortfolioAssetValuation:
    return PortfolioAssetValuation(
        asset=asset,
        role="CORE",
        price_usdt=Decimal("1"),
        spot_value_usdt=total_value_usdt,
        flexible_value_usdt=Decimal("0"),
        locked_value_usdt=Decimal("0"),
        total_value_usdt=total_value_usdt,
        allocation_pct=Decimal("0"),
        target_pct=None,
        gap_pct=None,
        rebalance_action=rebalance_action,
    )


def _portfolio(*assets: PortfolioAssetValuation) -> PortfolioAnalysis:
    total = sum((asset.total_value_usdt for asset in assets), Decimal("0"))
    return PortfolioAnalysis(
        total_value_usdt=total,
        spot_value_usdt=total,
        flexible_value_usdt=Decimal("0"),
        locked_value_usdt=Decimal("0"),
        liquid_value_usdt=total,
        locked_pct=Decimal("0"),
        assets=assets,
        unpriced_assets=(),
        ignored_internal_assets=(),
        rebalance_summary="",
        liquidity_summary="",
    )


def _no_quote_balance() -> list[Balance]:
    return [Balance(asset="USDC", spot_free=Decimal("0"), flexible_amount=Decimal("0"))]


def test_protected_and_disallowed_assets_are_never_sourced():
    # BTC is protected and DOGE is not in allowed_source_assets; neither may ever be
    # recommended as a capital source no matter how overweight or valuable they are.
    portfolio = _portfolio(
        _asset("BTC", Decimal("5000"), rebalance_action="REDUCE"),
        _asset("DOGE", Decimal("500"), rebalance_action="REDUCE"),
        _asset("SOL", Decimal("200"), rebalance_action="REDUCE"),
    )
    advisor = CapitalSourcingAdvisor(_config())

    plan = advisor.plan(_no_quote_balance(), portfolio, needed_usdt=Decimal("15"))

    sourced_assets = {item.asset for item in plan.items}
    assert sourced_assets == {"SOL"}


def test_per_run_cap_limits_total_sourced_even_when_more_is_missing():
    portfolio = _portfolio(_asset("SOL", Decimal("200"), rebalance_action="REDUCE"))
    advisor = CapitalSourcingAdvisor(_config())

    plan = advisor.plan(_no_quote_balance(), portfolio, needed_usdt=Decimal("100"))

    total_sourced = sum((item.value_usdt for item in plan.items), Decimal("0"))
    assert total_sourced == Decimal("20.00")  # max_source_value_usdt_per_run, not the full 100 missing


def test_per_asset_source_never_drops_the_asset_below_its_configured_reserve():
    # min_remaining_pct_per_asset=70% of a 200 USDC position means at least 140 must
    # stay behind; with a high per-run cap and per-asset pct cap that constraint binds.
    portfolio = _portfolio(_asset("SOL", Decimal("200"), rebalance_action="REDUCE"))
    advisor = CapitalSourcingAdvisor(
        _config(max_source_value_usdt_per_run="1000", max_source_pct_per_asset="50", max_total_source_pct_per_run="100")
    )

    plan = advisor.plan(_no_quote_balance(), portfolio, needed_usdt=Decimal("500"))

    assert len(plan.items) == 1
    item = plan.items[0]
    remaining_after_source = Decimal("200") - item.value_usdt
    assert remaining_after_source >= Decimal("140")  # 70% of 200
    assert remaining_after_source >= Decimal("50")  # absolute floor


def test_disabled_capital_sourcing_recommends_nothing():
    portfolio = _portfolio(_asset("SOL", Decimal("200"), rebalance_action="REDUCE"))
    advisor = CapitalSourcingAdvisor(_config(enabled=False))

    plan = advisor.plan(_no_quote_balance(), portfolio, needed_usdt=Decimal("100"))

    assert plan.recommended is False
    assert plan.items == ()


def test_no_sourcing_plan_when_available_balance_already_covers_the_need():
    portfolio = _portfolio(_asset("SOL", Decimal("200"), rebalance_action="REDUCE"))
    advisor = CapitalSourcingAdvisor(_config())
    balances = [Balance(asset="USDC", spot_free=Decimal("50"), flexible_amount=Decimal("0"))]

    plan = advisor.plan(balances, portfolio, needed_usdt=Decimal("10"))

    assert plan.recommended is False
    assert plan.items == ()
