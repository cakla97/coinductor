from coinductor.user_profile_service import UserProfileService


def test_user_profile_service_reports_missing_profile(tmp_path) -> None:
    snapshot = UserProfileService(tmp_path / "state" / "user_profile.toml").inspect()

    assert snapshot.configured is False
    assert "Safe defaults" in snapshot.summary


def test_user_profile_service_saves_safe_default_snapshot(tmp_path) -> None:
    service = UserProfileService(tmp_path / "state" / "user_profile.toml")

    snapshot = service.save_safe_default("FIRST_PORTFOLIO")

    assert snapshot.configured is True
    assert "FIRST_PORTFOLIO" in snapshot.summary
    assert "BINANCE" in snapshot.summary
    assert any(item["name"] == "Spot trades" and item["value"] == "Disabled" for item in snapshot.fields)
    assert any(item["name"] == "Grid" and item["value"] == "Disabled" for item in snapshot.fields)
    assert any(item["name"] == "Create account" for item in snapshot.exchange_steps)
    assert any(item["name"] == "Deposit funds" for item in snapshot.exchange_steps)


def test_user_profile_service_existing_portfolio_skips_account_creation(tmp_path) -> None:
    service = UserProfileService(tmp_path / "state" / "user_profile.toml")

    snapshot = service.save_safe_default("EXISTING_PORTFOLIO")

    assert any(item["name"] == "Existing account" for item in snapshot.exchange_steps)
    assert not any(item["name"] == "Create account" for item in snapshot.exchange_steps)


def test_user_profile_service_saves_guided_snapshot(tmp_path) -> None:
    service = UserProfileService(tmp_path / "state" / "user_profile.toml")

    snapshot = service.save_guided(
        onboarding_path="EXISTING_PORTFOLIO",
        management_style="ACTIVE",
        automation_level="GUARDED_AUTOMATION",
        run_cadence="DAILY",
        base_currency="USDC",
        use_bots=True,
        allow_spot_trades=True,
        max_drawdown_comfort_pct=20,
    )

    assert snapshot.configured is True
    assert "GUIDED" in snapshot.summary
    assert any(item["name"] == "Automation" and item["value"] == "GUARDED_AUTOMATION" for item in snapshot.fields)
    assert any(item["name"] == "Spot trades" and item["value"] == "Allowed" for item in snapshot.fields)
    assert any(item["name"] == "Grid" and item["value"] == "Enabled" for item in snapshot.fields)
    assert any(item["name"] == "Drawdown comfort" and item["value"] == "20%" for item in snapshot.fields)


def test_user_profile_service_current_profile_uses_in_memory_fallback(tmp_path) -> None:
    path = tmp_path / "state" / "user_profile.toml"
    service = UserProfileService(path)

    profile = service.current_profile("FIRST_PORTFOLIO")

    assert profile.onboarding_path == "FIRST_PORTFOLIO"
    assert not path.exists()
