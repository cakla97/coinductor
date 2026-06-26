from trading_agent.safety_state import SafetyState, SafetyStateStore, stage_at_least


def test_default_safety_state_is_setup_and_blocks_live_actions(tmp_path) -> None:
    state = SafetyStateStore(tmp_path / "state" / "app_safety_state.toml").load()

    assert state.stage == "SETUP"
    assert state.allows_live_preview is False
    assert state.allows_live_submit is False


def test_safety_state_roundtrip_preview_only(tmp_path) -> None:
    store = SafetyStateStore(tmp_path / "state" / "app_safety_state.toml")

    store.save(SafetyState(stage="PREVIEW_ONLY", detail="Preview enabled."))
    state = store.load()

    assert state.stage == "PREVIEW_ONLY"
    assert state.allows_live_preview is True
    assert state.allows_live_submit is False
    assert stage_at_least("LIVE_ENABLED", "PREVIEW_ONLY") is True
    assert stage_at_least("SETUP", "PREVIEW_ONLY") is False


def test_unknown_safety_stage_falls_back_to_setup(tmp_path) -> None:
    path = tmp_path / "state" / "app_safety_state.toml"
    path.parent.mkdir()
    path.write_text('[safety_state]\nstage = "UNSAFE"\n', encoding="utf-8")

    state = SafetyStateStore(path).load()

    assert state.stage == "SETUP"
    assert state.allows_live_submit is False
