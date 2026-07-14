from coinductor.local_data_reset import LocalDataResetService


def test_local_data_reset_preview_lists_expected_groups(tmp_path) -> None:
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "user_profile.toml").write_text("[user_profile]\n", encoding="utf-8")

    snapshot = LocalDataResetService(tmp_path).preview()

    codes = {item["code"] for item in snapshot.items}
    assert "PROFILE" in codes
    assert "DATABASE" in codes
    assert "REPORTS" in codes
    assert "RESEARCH" in codes
    assert "AI_CHAT_HISTORY" in codes
    assert "ENV" in codes
    assert any(item["code"] == "PROFILE" and item["default"] == "true" for item in snapshot.items)
    assert any(item["code"] == "PROFILE" and item["status"] == "Present" for item in snapshot.items)
    assert any(item["code"] == "PROFILE" and "app_ui_state.toml" in item["paths"] for item in snapshot.items)
    assert any(item["code"] == "ENV" and ".env" in item["paths"] for item in snapshot.items)
    assert any(
        item["code"] == "AI_CHAT_HISTORY" and "assistant_history.json" in item["paths"]
        for item in snapshot.items
    )
