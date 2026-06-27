from coinductor.first_portfolio_planner import FirstPortfolioPlanner
from trading_agent.user_profile import guided_profile, safe_default_profile


def test_first_portfolio_planner_is_unavailable_for_existing_portfolio() -> None:
    profile = safe_default_profile("EXISTING_PORTFOLIO")

    plan = FirstPortfolioPlanner().plan(profile)

    assert plan.available is False
    assert not plan.allocation


def test_first_portfolio_planner_creates_balanced_starting_plan() -> None:
    profile = guided_profile(
        onboarding_path="FIRST_PORTFOLIO",
        management_style="BALANCED",
        automation_level="RECOMMEND_ONLY",
        run_cadence="TWICE_WEEKLY",
        base_currency="USDC",
        locale="cs-CZ",
        use_bots=True,
        allow_spot_trades=False,
        max_drawdown_comfort_pct=15,
        planned_deposit_amount=500,
    )

    plan = FirstPortfolioPlanner().plan(profile)

    assert plan.available is True
    assert "500 CZK" in plan.summary
    assert any(item["name"] == "Reserve" and item["value"] == "80 CZK" for item in plan.funding)
    assert any(item["asset"] == "BTC" and item["target"] == "40%" for item in plan.allocation)
    assert any(item["asset"] == "BTC" and item["amount"] == "40% of converted USDC" for item in plan.allocation)
    assert any(item["asset"] == "WLD" and item["role"] == "Growth" for item in plan.allocation)
    assert any(item["name"] == "Execution" and "nikdy nezadává objednávky" in item["detail"] for item in plan.notes)


def test_first_portfolio_planner_uses_safe_default_budget() -> None:
    profile = safe_default_profile("FIRST_PORTFOLIO")

    plan = FirstPortfolioPlanner().plan(profile)

    assert plan.available is True
    assert "500 USD" in plan.summary
    assert any(item["asset"] == "ETH" and item["target"] == "30%" for item in plan.allocation)
