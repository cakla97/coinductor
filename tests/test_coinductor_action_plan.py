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
                # `code` mirrors SetupService: lookups match on it, not the
                # translated name.
                "code": "BINANCE_LIVE",
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


def test_challenge_hold_outcome_states_whether_an_order_happened(monkeypatch, tmp_path) -> None:
    """The old message only said the override "was evaluated", which left the
    user unsure whether a trade had been placed."""
    controller = _controller(monkeypatch, tmp_path)

    controller._challenged_symbol = "BTCUSDC"
    controller._decision = "HOLD"
    rejected = controller._challenge_outcome_message()
    assert "rejected" in rejected
    assert "No order was placed" in rejected

    controller._challenged_symbol = "BTCUSDC"
    controller._decision = "BUY"
    accepted = controller._challenge_outcome_message()
    assert "BUY" in accepted
    assert "Nothing was submitted" in accepted

    # Consumed once, so an ordinary run keeps its own completion message.
    assert controller._challenge_outcome_message() == ""


def test_challenge_hold_keeps_the_user_on_the_current_page(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller._decision = "HOLD"
    controller._manual_override_symbols = ["BTCUSDC"]
    controller._current_page = 3
    started: dict[str, object] = {}
    monkeypatch.setattr(
        controller, "_start_analysis", lambda *a, **kw: started.update(kw)
    )

    controller.challengeHold("BTCUSDC")

    # Was hardcoded to the Action Plan, which navigated away from the dialog.
    assert started["result_page"] == 3
    assert started["manual_override_symbol"] == "BTCUSDC"


def test_challenge_outcome_is_set_before_listeners_are_notified(monkeypatch, tmp_path) -> None:
    """challengeOutcome is notified by actionsChanged.

    Setting it after emitting left QML's text binding on the stale empty value
    while the visibility binding had already flipped true, rendering an empty
    banner.
    """
    controller = _controller(monkeypatch, tmp_path)
    controller._challenged_symbol = "BTCUSDC"
    controller._decision = "HOLD"
    seen: list[str] = []
    controller.actionsChanged.connect(lambda: seen.append(controller.challengeOutcome))

    controller._on_completed(_run("HOLD"))

    assert seen, "actionsChanged was not emitted"
    assert seen[0] != "", "listeners saw an empty outcome"
    assert "rejected" in seen[0]


def test_trade_card_reports_the_trade_verdict_not_the_run_decision(monkeypatch, tmp_path) -> None:
    """A recommended grid wins the run's decision type across every strategy.

    That value was rendered as the Trade card's own status, so a plain HOLD
    showed "GRID_BOT_RECOMMENDATION" and was coloured blocked - and because
    canSubmitLive was derived from it, an approved BUY lost its submit button
    whenever a grid was recommended in the same run.
    """
    controller = _controller(monkeypatch, tmp_path)
    state = _set_trade_state(controller, "BUY", live_enabled=True, key_ready=True)
    controller._decision = "GRID_BOT_RECOMMENDATION"  # what a grid-positive run reports

    card = next(item for item in controller._build_action_plan_items() if item["title"] == "Trade")

    assert card["status"] == "BUY", "the card must state the trade verdict"
    assert card["tone"] == "ready"
    assert card["canSubmitLive"] is True, "an approved BUY must keep its submit path"
    # The run-level decision stays visible, under a label that says what it is.
    assert {"label": "Run decision", "value": "GRID_BOT_RECOMMENDATION"} in card["parameters"]
    assert state is not None


def test_trade_card_shows_hold_as_hold_when_a_grid_is_recommended(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    _set_trade_state(controller, "HOLD", live_enabled=False, key_ready=False)
    controller._decision = "GRID_BOT_RECOMMENDATION"

    card = next(item for item in controller._build_action_plan_items() if item["title"] == "Trade")

    assert card["status"] == "HOLD"
    assert card["tone"] == "watch", "a HOLD is watched, not blocked"
    assert card["canSubmitLive"] is False


def test_bot_cards_say_why_setup_is_manual(monkeypatch, tmp_path) -> None:
    """The card hands over parameters to retype on Binance.

    Without the reason that reads as an unfinished feature - and the reason was
    only ever in the report and a wizard hint seen once during setup. The steps
    themselves are not persisted, so the app cannot show them.
    """
    controller = _controller(monkeypatch, tmp_path)
    _set_trade_state(controller, "HOLD", live_enabled=False, key_ready=False)
    controller._strategies = [
        {"type": "Spot Grid", "status": "READY", "detail": "BTCUSDC scored 82.", "parameters": []},
        {"type": "Rebalancing", "status": "BLOCKED", "detail": "Funding gap.", "parameters": []},
    ]

    cards = {item["title"]: item for item in controller._build_action_plan_items()}

    for name in ("Spot Grid", "Rebalancing"):
        assert "no public API" in cards[name]["detail"], name
    # The trade card is not a bot; it must not carry the note.
    assert "no public API" not in cards["Trade"]["detail"]


def test_the_manual_setup_note_is_translated(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    _set_trade_state(controller, "HOLD", live_enabled=False, key_ready=False)
    controller._strategies = [{"type": "Spot Grid", "status": "READY", "detail": "", "parameters": []}]

    card = next(i for i in controller._build_action_plan_items() if i["title"] == "Spot Grid")

    assert "veřejné API" in card["detail"], card["detail"]


def test_manual_steps_survive_the_whole_path_to_the_card(monkeypatch, tmp_path) -> None:
    """Steps are read from the journal and rebuilt into a new dict per card.

    They were persisted, read and rendered correctly and still arrived empty,
    because the card is assembled field by field and this one was not copied.
    """
    controller = _controller(monkeypatch, tmp_path)
    _set_trade_state(controller, "HOLD", live_enabled=False, key_ready=False)
    controller._strategies = [
        {
            "type": "Spot Grid",
            "status": "READY",
            "detail": "Suitable range.",
            "parameters": [],
            "manualSteps": ("Open Binance Home > Trading Bots > Spot Grid.", "Select BTCUSDC."),
        }
    ]

    card = next(i for i in controller._build_action_plan_items() if i["title"] == "Spot Grid")

    assert card["manualSteps"] == [
        "Open Binance Home > Trading Bots > Spot Grid.",
        "Select BTCUSDC.",
    ]
