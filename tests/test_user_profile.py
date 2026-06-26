from trading_agent.user_profile import UserProfileStore, safe_default_profile


def test_safe_default_profile_is_conservative() -> None:
    profile = safe_default_profile("FIRST_PORTFOLIO")

    assert profile.onboarding_path == "FIRST_PORTFOLIO"
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
    assert "allow_spot_trades = false" in rendered
