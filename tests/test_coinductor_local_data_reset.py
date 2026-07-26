
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
    assert any(
        item["code"] == "AI_CHAT_HISTORY" and "assistant_attachments" in item["paths"]
        for item in snapshot.items
    )


def test_execute_removes_only_the_selected_group(tmp_path) -> None:
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "user_profile.toml").write_text("[user_profile]\n", encoding="utf-8")
    (tmp_path / "state" / "app_ui_state.toml").write_text("[ui]\n", encoding="utf-8")
    (tmp_path / ".env").write_text("BINANCE_API_KEY=test\n", encoding="utf-8")
    service = LocalDataResetService(tmp_path)

    snapshot = service.execute(["PROFILE"])

    assert not (tmp_path / "state" / "user_profile.toml").exists()
    assert not (tmp_path / "state" / "app_ui_state.toml").exists()
    assert (tmp_path / ".env").exists()  # ENV group was not selected
    assert "state/user_profile.toml" in snapshot.summary
    assert any(item["code"] == "PROFILE" and item["status"] == "Not found yet" for item in snapshot.items)
    assert any(item["code"] == "ENV" and item["status"] == "Present" for item in snapshot.items)


def test_execute_removes_a_directory_group(tmp_path) -> None:
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "run-1.md").write_text("# report", encoding="utf-8")
    service = LocalDataResetService(tmp_path)

    service.execute(["REPORTS"])

    assert not (tmp_path / "reports").exists()


def test_execute_is_a_no_op_for_paths_that_do_not_exist(tmp_path) -> None:
    service = LocalDataResetService(tmp_path)

    snapshot = service.execute(["DATABASE"])

    assert "No selected local data group had anything to remove." in snapshot.summary


def test_execute_ignores_unknown_group_codes(tmp_path) -> None:
    (tmp_path / ".env").write_text("BINANCE_API_KEY=test\n", encoding="utf-8")
    service = LocalDataResetService(tmp_path)

    service.execute(["NOT_A_REAL_GROUP"])

    assert (tmp_path / ".env").exists()


def test_execute_refuses_to_delete_outside_the_project_root(tmp_path, monkeypatch) -> None:
    outside_dir = tmp_path.parent / "outside_guard_target"
    outside_dir.mkdir(exist_ok=True)
    canary = outside_dir / "do_not_delete.txt"
    canary.write_text("still here", encoding="utf-8")
    project_root = tmp_path / "project"
    project_root.mkdir()
    service = LocalDataResetService(project_root)
    monkeypatch.setattr(
        service,
        "_groups",
        lambda: (
            {
                "code": "ESCAPE_ATTEMPT",
                "name": "Escape attempt",
                "detail": "test",
                "default": False,
                "paths": (f"../{outside_dir.name}",),
            },
        ),
    )

    snapshot = service.execute(["ESCAPE_ATTEMPT"])

    assert canary.exists()
    assert "outside the project root" in snapshot.summary


def test_execute_refuses_to_delete_the_project_root_itself(tmp_path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    canary = project_root / "keep.txt"
    canary.write_text("still here", encoding="utf-8")
    service = LocalDataResetService(project_root)

    def _groups():
        return (
            {
                "code": "ROOT_ESCAPE",
                "name": "Root escape",
                "detail": "test",
                "default": False,
                "paths": (".",),
            },
        )

    service._groups = _groups

    snapshot = service.execute(["ROOT_ESCAPE"])

    assert project_root.exists()
    assert canary.exists()
    assert "resolves to the project root itself" in snapshot.summary
