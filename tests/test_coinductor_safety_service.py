from trading_agent.safety_state import SafetyState, SafetyStateStore

from coinductor.safety_service import SafetyService


def test_safety_service_default_snapshot_locks_preview_and_submit(tmp_path) -> None:
    snapshot = SafetyService(tmp_path / "state" / "app_safety_state.toml").inspect()

    assert snapshot.stage == "SETUP"
    assert snapshot.allows_live_preview is False
    assert snapshot.allows_live_submit is False
    assert any(item["name"] == "Orders" and item["status"] == "LOCKED" for item in snapshot.checks)


def test_safety_service_preview_only_allows_preview_not_submit(tmp_path) -> None:
    path = tmp_path / "state" / "app_safety_state.toml"
    SafetyStateStore(path).save(SafetyState(stage="PREVIEW_ONLY", detail="Preview only."))

    snapshot = SafetyService(path).inspect()

    assert snapshot.stage == "PREVIEW_ONLY"
    assert snapshot.allows_live_preview is True
    assert snapshot.allows_live_submit is False
    assert any(item["name"] == "Mainnet preview" and item["status"] == "AVAILABLE" for item in snapshot.checks)


def test_safety_service_requires_ordered_confirmed_transitions(tmp_path) -> None:
    service = SafetyService(tmp_path / "state" / "app_safety_state.toml")

    preview = service.transition("PREVIEW_ONLY", "Enable mainnet preview", live_key_verified=False)
    armed = service.transition("ARMED", "Arm guarded actions", live_key_verified=True)
    live = service.transition("LIVE_ENABLED", "Enable guarded live submit", live_key_verified=True)

    assert preview.stage == "PREVIEW_ONLY"
    assert armed.stage == "ARMED"
    assert live.stage == "LIVE_ENABLED"
    assert live.allows_live_submit is True


def test_safety_service_rejects_live_transition_without_verified_key(tmp_path) -> None:
    service = SafetyService(tmp_path / "state" / "app_safety_state.toml")
    service.transition("PREVIEW_ONLY", "Enable mainnet preview", live_key_verified=False)

    try:
        service.transition("ARMED", "Arm guarded actions", live_key_verified=False)
    except ValueError as exc:
        assert "Verify" in str(exc)
    else:
        raise AssertionError("ARMED transition should require a verified live key")


def test_recommend_only_profile_vetoes_submit_even_when_live_enabled(tmp_path) -> None:
    """RECOMMEND_ONLY promises Coinductor never acts, so it overrides the stage."""
    path = tmp_path / "state" / "app_safety_state.toml"
    SafetyStateStore(path).save(SafetyState(stage="LIVE_ENABLED", detail="Live."))
    service = SafetyService(path)
    service.automation_allows_submit = False

    snapshot = service.inspect()

    assert snapshot.stage == "LIVE_ENABLED"
    assert snapshot.allows_live_preview is True, "previews are still recommendations"
    assert snapshot.allows_live_submit is False
    orders = next(item for item in snapshot.checks if item["name"] == "Orders")
    assert orders["status"] == "LOCKED"
    # The user armed the stage, so the detail must point at the real blocker.
    assert "profile" in orders["detail"].lower()


def test_automation_veto_cannot_grant_submit_the_stage_withholds(tmp_path) -> None:
    service = SafetyService(tmp_path / "state" / "app_safety_state.toml")
    service.automation_allows_submit = True

    assert service.inspect().allows_live_submit is False


def test_recommend_only_profile_blocks_arming_live_submit(tmp_path) -> None:
    service = SafetyService(tmp_path / "state" / "app_safety_state.toml")
    service.transition("PREVIEW_ONLY", "Enable mainnet preview", live_key_verified=False)
    service.transition("ARMED", "Arm guarded actions", live_key_verified=True)
    service.automation_allows_submit = False

    try:
        service.transition("LIVE_ENABLED", "Enable guarded live submit", live_key_verified=True)
    except ValueError as exc:
        assert "Recommendations only" in str(exc)
    else:
        raise AssertionError("LIVE_ENABLED must not be reachable under RECOMMEND_ONLY")

    assert SafetyStateStore(service.store.path).load().stage == "ARMED"


def test_safety_service_lock_returns_to_preview_only(tmp_path) -> None:
    service = SafetyService(tmp_path / "state" / "app_safety_state.toml")
    service.transition("PREVIEW_ONLY", "Enable mainnet preview", live_key_verified=False)
    service.transition("ARMED", "Arm guarded actions", live_key_verified=True)
    service.transition("LIVE_ENABLED", "Enable guarded live submit", live_key_verified=True)

    locked = service.lock_live_submit()

    assert locked.stage == "PREVIEW_ONLY"
    assert locked.allows_live_preview is True
    assert locked.allows_live_submit is False
