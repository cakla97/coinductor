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

    preview = service.transition("PREVIEW_ONLY", "ENABLE_MAINNET_PREVIEW", live_key_verified=False)
    armed = service.transition("ARMED", "ARM_GUARDED_ACTIONS", live_key_verified=True)
    live = service.transition("LIVE_ENABLED", "ENABLE_LIVE_GUARDED_SUBMIT", live_key_verified=True)

    assert preview.stage == "PREVIEW_ONLY"
    assert armed.stage == "ARMED"
    assert live.stage == "LIVE_ENABLED"
    assert live.allows_live_submit is True


def test_safety_service_rejects_live_transition_without_verified_key(tmp_path) -> None:
    service = SafetyService(tmp_path / "state" / "app_safety_state.toml")
    service.transition("PREVIEW_ONLY", "ENABLE_MAINNET_PREVIEW", live_key_verified=False)

    try:
        service.transition("ARMED", "ARM_GUARDED_ACTIONS", live_key_verified=False)
    except ValueError as exc:
        assert "Verify" in str(exc)
    else:
        raise AssertionError("ARMED transition should require a verified live key")


def test_safety_service_lock_returns_to_preview_only(tmp_path) -> None:
    service = SafetyService(tmp_path / "state" / "app_safety_state.toml")
    service.transition("PREVIEW_ONLY", "ENABLE_MAINNET_PREVIEW", live_key_verified=False)
    service.transition("ARMED", "ARM_GUARDED_ACTIONS", live_key_verified=True)
    service.transition("LIVE_ENABLED", "ENABLE_LIVE_GUARDED_SUBMIT", live_key_verified=True)

    locked = service.lock_live_submit()

    assert locked.stage == "PREVIEW_ONLY"
    assert locked.allows_live_preview is True
    assert locked.allows_live_submit is False
