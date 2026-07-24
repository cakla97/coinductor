from decimal import Decimal

from coinductor.models import (
    DesktopRunResult,
    DesktopSnapshot,
    ReadinessSnapshot,
    SafetySnapshot,
    SetupSnapshot,
    UserProfileSnapshot,
)
from coinductor.readiness_service import ReadinessService


def test_readiness_blocks_without_profile_and_read_only_keys() -> None:
    snapshot = _readiness(
        setup=_setup(read_only_status="WARN"),
        profile=_profile(configured=False),
        safety=_safety(),
        desktop=_desktop(has_assets=False),
        connection_status="Not checked",
    )

    assert snapshot.summary == "0/5 readiness step(s) ready"
    assert "Choose safe defaults" in snapshot.next_step
    assert snapshot.action_code == "GUIDE_PROFILE"
    assert snapshot.action_label == "Guide me"
    assert snapshot.action_enabled is True
    assert _step(snapshot, "Profile")["status"] == "NEXT"
    assert _step(snapshot, "Binance read-only")["status"] == "BLOCKED"
    assert _step(snapshot, "Guarded live execution")["status"] == "LOCKED"


def test_readiness_marks_profile_connection_and_classification_ready() -> None:
    snapshot = _readiness(
        setup=_setup(read_only_status="PASS"),
        profile=_profile(configured=True),
        safety=_safety(allows_preview=True),
        desktop=_desktop(has_assets=True),
        connection_status="Connected",
    )

    assert snapshot.summary == "4/5 readiness step(s) ready"
    assert "Live submit stays locked" in snapshot.next_step
    assert snapshot.action_code == "OPEN_PORTFOLIO"
    assert snapshot.action_label == "Review portfolio roles"
    assert snapshot.action_enabled is True
    assert _step(snapshot, "Profile")["status"] == "READY"
    assert _step(snapshot, "Binance read-only")["status"] == "READY"
    assert _step(snapshot, "Portfolio classification")["status"] == "READY"
    assert _step(snapshot, "Mainnet preview")["status"] == "READY"


def test_readiness_suggests_connection_check_when_keys_exist() -> None:
    snapshot = _readiness(
        setup=_setup(read_only_status="PASS"),
        profile=_profile(configured=True),
        safety=_safety(),
        desktop=_desktop(has_assets=False),
        connection_status="Not checked",
    )

    assert snapshot.action_code == "CHECK_BINANCE"
    assert snapshot.action_label == "Run read-only check"
    assert snapshot.action_enabled is True


def test_readiness_suggests_classification_after_connection() -> None:
    snapshot = _readiness(
        setup=_setup(read_only_status="PASS"),
        profile=_profile(configured=True),
        safety=_safety(),
        desktop=_desktop(has_assets=False),
        connection_status="Connected",
    )

    assert snapshot.action_code == "RUN_CLASSIFICATION"
    assert snapshot.action_label == "Run classification"
    assert snapshot.action_enabled is True


def _readiness(
    setup: SetupSnapshot,
    profile: UserProfileSnapshot,
    safety: SafetySnapshot,
    desktop: DesktopSnapshot,
    connection_status: str,
) -> ReadinessSnapshot:
    return ReadinessService().inspect(setup, profile, safety, desktop, connection_status)


def _setup(read_only_status: str) -> SetupSnapshot:
    # `code` mirrors SetupService: readiness matches on it, not the translated name.
    checks = (
        {"code": "", "name": "Python", "status": "PASS", "detail": "3.14", "group": "Runtime"},
        {"code": "", "name": "Configuration", "status": "PASS", "detail": "Valid", "group": "Runtime"},
        {
            "code": "BINANCE_READONLY",
            "name": "Binance read-only",
            "status": read_only_status,
            "detail": "Configured" if read_only_status == "PASS" else "Required",
            "group": "Binance",
        },
    )
    return SetupSnapshot(
        checks=checks,
        passed=sum(item["status"] == "PASS" for item in checks),
        warnings=sum(item["status"] == "WARN" for item in checks),
        blocked=sum(item["status"] == "BLOCK" for item in checks),
    )


def _profile(configured: bool) -> UserProfileSnapshot:
    return UserProfileSnapshot(
        configured=configured,
        summary="Configured" if configured else "Missing",
        fields=(),
        exchange_steps=(),
    )


def _safety(allows_preview: bool = False, allows_submit: bool = False) -> SafetySnapshot:
    return SafetySnapshot(
        stage="PREVIEW_ONLY" if allows_preview else "SETUP",
        label="Preview Only" if allows_preview else "Setup",
        detail="Preview enabled" if allows_preview else "Setup mode",
        allows_live_preview=allows_preview,
        allows_live_submit=allows_submit,
        checks=(),
    )


def _desktop(has_assets: bool) -> DesktopSnapshot:
    return DesktopSnapshot(
        latest_run=_run() if has_assets else None,
        portfolio_assets=({"asset": "BTC", "value": "100.00 USDC", "role": "PROTECTED_CORE"},) if has_assets else (),
        strategies=(),
        run_history=(),
    )


def _run() -> DesktopRunResult:
    return DesktopRunResult(
        run_id=1,
        status="DONE",
        report_path="reports/run-1.md",
        decision="HOLD",
        decision_summary="No trade.",
        risk_approved=False,
        risk_reason="Hold",
        portfolio_value=Decimal("100"),
        liquid_value=Decimal("0"),
        locked_value=Decimal("100"),
        ai_summary="",
        actions=(),
    )


def _step(snapshot: ReadinessSnapshot, name: str) -> dict[str, str]:
    return next(item for item in snapshot.steps if item["name"] == name)
