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
    assert any(item["name"] == "Spot trades" and item["value"] == "Disabled" for item in snapshot.fields)
    assert any(item["name"] == "Grid" and item["value"] == "Disabled" for item in snapshot.fields)
