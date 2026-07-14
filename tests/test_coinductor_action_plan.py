from dataclasses import replace
from decimal import Decimal

import pytest

pytest.importorskip("PySide6")

from coinductor.controller import AppController
from coinductor.models import (
    DesktopRunResult,
    DesktopSnapshot,
    SafetySnapshot,
    SetupSnapshot,
)


def _controller(monkeypatch, tmp_path) -> AppController:
    monkeypatch.chdir(tmp_path)
    return AppController()


def _run(action: str) -> DesktopRunResult:
    return DesktopRunResult(
        run_id=1,
        status="OK",
        report_path="report.md",
        decision=action,
        decision_summary=f"{action} test decision.",
        risk_approved=True,
        risk_reason="Within limits.",
        portfolio_value=Decimal("500"),
        liquid_value=Decimal("100"),
        locked_value=Decimal("400"),
        ai_summary="",
        actions=(),
        trade_proposal={
            "symbol": "BTCUSDC",
            "action": action,
            "confidence": "0.80",
            "quoteAmount": "15.00 USDC",
            "reason": f"{action} test proposal.",
        },
    )


def _set_trade_state(controller: AppController, action: str, *, live_enabled: bool, key_ready: bool) -> dict:
    latest = _run(action)
    controller._decision = action
    controller._decision_summary = latest.decision_summary
    controller._snapshot = DesktopSnapshot(latest, (), (), (), None)
    controller._strategies = []
    controller._actions = []
    controller._safety_snapshot = SafetySnapshot(
        stage="LIVE_ENABLED" if live_enabled else "PREVIEW_ONLY",
        label="Live enabled" if live_enabled else "Preview only",
        detail="Test safety state.",
        allows_live_preview=True,
        allows_live_submit=live_enabled,
        checks=(),
    )
    controller._setup_snapshot = SetupSnapshot(
        checks=(
            {
                "name": "Binance live trading",
                "status": "PASS" if key_ready else "WARN",
                "detail": "Test key state.",
                "group": "Setup",
            },
        ),
        passed=1 if key_ready else 0,
        warnings=0 if key_ready else 1,
        blocked=0,
    )
    controller._live_trading_check_status = "Verified" if key_ready else "Not checked"
    return controller._build_action_plan_items()[0]


def test_hold_trade_is_review_only(monkeypatch, tmp_path) -> None:
    card = _set_trade_state(_controller(monkeypatch, tmp_path), "HOLD", live_enabled=True, key_ready=True)

    assert card["tone"] == "watch"
    assert card["canSubmitLive"] is False
    assert card["submitEnabled"] is False


def test_snapshot_hydrates_deterministic_trade_before_building_cards(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    latest = replace(_run("HOLD"), trade_proposal=None)
    controller._snapshot = DesktopSnapshot(latest, (), (), (), None)

    controller._apply_snapshot()

    card = controller.actionPlanItems[0]
    assert card["status"] == "HOLD"
    assert card["tone"] == "watch"
    assert card["parameters"][0]["value"] == "HOLD"


def test_buy_trade_stays_locked_before_live_stage(monkeypatch, tmp_path) -> None:
    card = _set_trade_state(_controller(monkeypatch, tmp_path), "BUY", live_enabled=False, key_ready=True)

    assert card["tone"] == "ready"
    assert card["canSubmitLive"] is True
    assert card["submitEnabled"] is False
    assert "LIVE_ENABLED" in card["submitBlockedReason"]


def test_buy_trade_submit_requires_live_stage_and_ready_key(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)

    key_locked = _set_trade_state(controller, "BUY", live_enabled=True, key_ready=False)
    ready = _set_trade_state(controller, "BUY", live_enabled=True, key_ready=True)

    assert key_locked["submitEnabled"] is False
    assert "key" in key_locked["submitBlockedReason"].lower()
    assert ready["submitEnabled"] is True
    assert ready["submitBlockedReason"] == ""


def test_buy_trade_requires_fresh_live_permission_check(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    card = _set_trade_state(controller, "BUY", live_enabled=True, key_ready=True)
    controller._live_trading_check_status = "Not checked"

    card = controller._build_action_plan_items()[0]

    assert card["submitEnabled"] is False
    assert "this app session" in card["submitBlockedReason"]


def test_live_lifecycle_is_nested_in_trade_card(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    _set_trade_state(controller, "HOLD", live_enabled=False, key_ready=False)
    lifecycle = {
        "title": "Live position lifecycle",
        "status": "Protected",
        "tone": "ready",
        "detail": "OCO is active.",
        "parameters": (),
        "lifecycleSteps": (),
        "primaryLabel": "View lifecycle",
        "actionCode": "REVIEW_LIFECYCLE",
    }
    controller._snapshot = DesktopSnapshot(
        controller._snapshot.latest_run,
        (),
        (),
        (),
        None,
        False,
        lifecycle,
    )

    cards = controller._build_action_plan_items()

    assert cards[0]["title"] == "Trade"
    assert cards[0]["liveLifecycle"]["status"] == "Protected"
    assert all(card["title"] != "Live position lifecycle" for card in cards[1:])


def test_active_strategy_refresh_returns_to_monitor_without_ai(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    captured = {}

    def capture(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    controller._start_analysis = capture

    controller.refreshActiveStrategies()

    assert captured["args"] == ("REAL", False, False, False)
    assert captured["kwargs"]["result_page"] == 4
    assert "monitoring refreshed" in captured["kwargs"]["completion_message"].lower()


def test_action_plan_surfaces_only_active_bots_requiring_attention(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller._active_strategies = [
        {"type": "Spot Grid", "name": "BTC Grid", "health": "Healthy", "state": "In Range"},
        {
            "type": "Rebalancing",
            "name": "Core Basket",
            "health": "Action required",
            "state": "Threshold Reached",
        },
    ]

    cards = controller._build_action_plan_items()
    alert = next(card for card in cards if card["title"] == "Active bot attention")

    assert alert["status"] == "Review required"
    assert alert["actionCode"] == "OPEN_ACTIVE_STRATEGIES"
    assert "Core Basket" in alert["detail"]
    assert "BTC Grid" not in alert["detail"]
