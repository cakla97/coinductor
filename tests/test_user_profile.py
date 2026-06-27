from trading_agent.user_profile import UserProfileStore, guided_profile, safe_default_profile


def test_safe_default_profile_is_conservative() -> None:
    profile = safe_default_profile("FIRST_PORTFOLIO")

    assert profile.onboarding_path == "FIRST_PORTFOLIO"
    assert profile.exchange == "BINANCE"
    assert profile.setup_mode == "SAFE_DEFAULTS"
    assert profile.experience == "BEGINNER"
    assert profile.management_style == "CONSERVATIVE"
    assert profile.automation_level == "RECOMMEND_ONLY"
    assert profile.use_earn is True
    assert profile.use_rebalancing is True
    assert profile.use_grid is False
    assert profile.allow_spot_trades is False


def test_user_profile_store_roundtrip(tmp_path) -> None:
    store = UserProfileStore(tmp_path / "state" / "user_profile.toml")

    saved = store.save_safe_default("EXISTING_PORTFOLIO")
    loaded = store.load()

    assert loaded == saved
    rendered = (tmp_path / "state" / "user_profile.toml").read_text(encoding="utf-8")
    assert 'setup_mode = "SAFE_DEFAULTS"' in rendered
    assert 'exchange = "BINANCE"' in rendered
    assert "allow_spot_trades = false" in rendered


def test_guided_profile_balanced_is_guarded_but_not_active_automation() -> None:
    profile = guided_profile(
        onboarding_path="FIRST_PORTFOLIO",
        management_style="BALANCED",
        automation_level="ACTIVE_AUTOMATION",
        run_cadence="TWICE_WEEKLY",
        base_currency="usdc",
        use_bots=True,
        allow_spot_trades=True,
        max_drawdown_comfort_pct=15,
        planned_deposit_amount=500,
    )

    assert profile.setup_mode == "GUIDED"
    assert profile.management_style == "BALANCED"
    assert profile.automation_level == "GUARDED_AUTOMATION"
    assert profile.base_currency == "USDC"
    assert profile.planned_deposit_amount == 500.0
    assert profile.use_rebalancing is True
    assert profile.use_grid is False
    assert profile.allow_spot_trades is True


def test_guided_profile_recommend_only_blocks_spot_trades() -> None:
    profile = guided_profile(
        onboarding_path="EXISTING_PORTFOLIO",
        management_style="ACTIVE",
        automation_level="RECOMMEND_ONLY",
        run_cadence="DAILY",
        base_currency="EUR",
        use_bots=True,
        allow_spot_trades=True,
        max_drawdown_comfort_pct=50,
    )

    assert profile.automation_level == "RECOMMEND_ONLY"
    assert profile.use_grid is True
    assert profile.allow_spot_trades is False
    assert profile.max_drawdown_comfort_pct == 25.0
