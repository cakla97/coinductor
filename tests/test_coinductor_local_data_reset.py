
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
    # Renamed from ENV: the group now also clears the OS keychain.
    assert "CREDENTIALS" in codes
    assert any(item["code"] == "PROFILE" and item["default"] == "true" for item in snapshot.items)
    assert any(item["code"] == "PROFILE" and item["status"] == "Present" for item in snapshot.items)
    assert any(item["code"] == "PROFILE" and "app_ui_state.toml" in item["paths"] for item in snapshot.items)
    assert any(item["code"] == "CREDENTIALS" and ".env" in item["paths"] for item in snapshot.items)
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
    assert (tmp_path / ".env").exists()  # CREDENTIALS group was not selected
    assert "state/user_profile.toml" in snapshot.summary
    assert any(item["code"] == "PROFILE" and item["status"] == "Not found yet" for item in snapshot.items)
    assert any(item["code"] == "CREDENTIALS" and item["status"] == "Present" for item in snapshot.items)


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


def test_selecting_every_group_leaves_nothing_behind(tmp_path) -> None:
    """The whole point of the screen: 'remove everything' must remove everything.

    REPORTS used to list only "reports" while app.reports_dir is
    "outputs/reports", so a user who ticked every box still had every report
    they had ever generated sitting on disk.
    """
    files = (
        "state/user_profile.toml",
        "state/app_ui_state.toml",
        "state/app_safety_state.toml",
        "state/asset_policy_overrides.toml",
        "state/active_strategies.toml",
        "state/grid_registry.toml",
        "state/rebalancing_registry.toml",
        "state/assistant_history.json",
        "state/assistant_attachments/shot.png",
        "work/trading_agent.sqlite3",
        "outputs/reports/2026-07-26_run-1.md",
        "research/notes/note.md",
        "research/requests/req.json",
        # Generated by Export diagnostics; survived a "delete everything" that
        # the screen describes as a full local reset.
        "outputs/diagnostics/coinductor-diagnostics-20260727T121523Z.txt",
        "config.toml",
        ".env",
    )
    for name in files:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")

    service = LocalDataResetService(tmp_path)
    service.execute([item["code"] for item in service.preview().items])

    survivors = sorted(
        str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*") if path.is_file()
    )
    assert not survivors, f"still on disk after deleting everything: {survivors}"


def test_the_credentials_group_also_clears_the_os_keychain(tmp_path, monkeypatch) -> None:
    """Deleting only .env would leave the most sensitive data of all behind.

    Keys normally live in the OS credential store, which the uninstaller does
    not touch either, so this screen is the only way to remove them.
    """
    from coinductor.secret_store import SecretStore

    monkeypatch.setenv("COINDUCTOR_DISABLE_KEYCHAIN", "1")
    env_file = tmp_path / ".env"
    store = SecretStore(env_path=env_file)
    store.set_many({"BINANCE_API_KEY": "k", "BINANCE_API_SECRET": "s"})
    assert env_file.exists()

    LocalDataResetService(tmp_path).execute(["CREDENTIALS"])

    assert not env_file.exists()
    assert store.stored_keys() == ()
