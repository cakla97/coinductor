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
