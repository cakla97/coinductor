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
    assert any(item["asset"] == "BTC" and item["targetPct"] == 40 for item in plan.allocation)
    assert any(item["asset"] == "BTC" and item["amount"] == "40% of converted USDC" for item in plan.allocation)
    assert any(item["asset"] == "WLD" and item["role"] == "Growth" for item in plan.allocation)
    # Prose follows the language argument, not the profile locale - see
    # test_currency_follows_the_locale_and_prose_follows_the_language.
    assert any(item["name"] == "Execution" and "never places orders" in item["detail"] for item in plan.notes)


def test_currency_follows_the_locale_and_prose_follows_the_language() -> None:
    """Two axes that used to be one, which is why the panel read English.

    profile.locale is a regional fact: someone in Czechia deposits CZK whatever
    language they read in. The prose was keyed off it too, so a Czech screen
    showed an English plan whenever the profile said en-US - which is the
    default, and what the tester actually had.
    """
    czech_region = guided_profile(
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

    english = FirstPortfolioPlanner().plan(czech_region, "en")
    czech = FirstPortfolioPlanner().plan(czech_region, "cs")

    # Same region, so the same money in both.
    assert "500 CZK" in english.summary and "500 CZK" in czech.summary
    # Different language, so different prose - and every label with it.
    assert "Start with" in english.summary
    assert "Začněte s" in czech.summary
    assert any(item["name"] == "Reserve" for item in english.funding)
    assert any(item["name"] == "Rezerva" for item in czech.funding)
    assert any(item["role"] == "Growth" for item in english.allocation)
    assert any(item["role"] == "Růstové" for item in czech.allocation)
    assert any(item["value"] == "Twice weekly" for item in english.steps)
    assert any(item["value"] == "Dvakrát týdně" for item in czech.steps)

    # A US profile read in Czech: dollars, Czech words.
    us_region = guided_profile(
        onboarding_path="FIRST_PORTFOLIO",
        management_style="BALANCED",
        automation_level="RECOMMEND_ONLY",
        run_cadence="DAILY",
        base_currency="USDC",
        locale="en-US",
        use_bots=True,
        allow_spot_trades=False,
        max_drawdown_comfort_pct=15,
        planned_deposit_amount=500,
    )
    mixed = FirstPortfolioPlanner().plan(us_region, "cs")
    assert "500 USD" in mixed.summary
    assert "Začněte s" in mixed.summary


def test_no_field_of_the_czech_plan_is_left_in_english() -> None:
    """The panel is built from these three lists; a literal anywhere shows.

    Checked by value rather than by key, because the English literals that
    started this were spread over labels, short values and details alike.
    """
    profile = guided_profile(
        onboarding_path="FIRST_PORTFOLIO",
        management_style="ACTIVE",
        automation_level="RECOMMEND_ONLY",
        run_cadence="WEEKLY",
        base_currency="USDC",
        locale="cs-CZ",
        use_bots=True,
        allow_spot_trades=False,
        max_drawdown_comfort_pct=15,
        planned_deposit_amount=500,
    )

    plan = FirstPortfolioPlanner().plan(profile, "cs")

    # Product names stay English on purpose, so "Rebalancing bota" is correct
    # Czech; these are phrases that only appear in the English wording.
    english_only = (
        "Deposit", "Reserve", "Initial deployment", "Fund Binance", "Buy basket",
        "Enable Earn", "Review rhythm", "Manual", "Optional", "Later", "Manual first",
        "Core", "Utility", "Growth", "of converted", "Execution",
        "can be considered after", "is below the usual", "stays disabled",
        "can be reviewed later",
    )
    rows = [*plan.funding, *plan.steps, *plan.notes, *plan.allocation]
    offenders = [
        f"{field}={value!r}"
        for row in rows
        for field, value in row.items()
        if isinstance(value, str) and any(term in value for term in english_only)
    ]
    assert offenders == [], "English left in the Czech plan:\n  " + "\n  ".join(offenders)


def test_first_portfolio_planner_uses_safe_default_budget() -> None:
    profile = safe_default_profile("FIRST_PORTFOLIO")

    plan = FirstPortfolioPlanner().plan(profile)

    assert plan.available is True
    assert "500 USD" in plan.summary
    assert any(item["asset"] == "ETH" and item["target"] == "30%" for item in plan.allocation)
