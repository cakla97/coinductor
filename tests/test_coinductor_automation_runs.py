"""The scheduled run, from the controller's side.

Two properties matter more than the rest: it can never submit, and it must not
take the window away from whoever is using it. Both are asserted here rather
than left to the shape of the code.
"""

import shutil
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from coinductor.automation import apply_automation_to_config
from coinductor.controller import AppController
from trading_agent.config import default_config_path

TEMPLATE = Path(__file__).resolve().parents[1] / "config.example.toml"


@pytest.fixture(autouse=True)
def _qt_application():
    """A QTimer cannot become active without an application instance.

    Without this the timer assertions below pass their interval check and fail
    on isActive - which looks like the feature is broken rather than the test.
    """
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])


def _controller(monkeypatch, tmp_path) -> AppController:
    # A real config in the working directory: without one every write lands on
    # a path that does not exist and is silently discarded, which would let
    # these tests pass against a feature that does nothing.
    shutil.copy(TEMPLATE, tmp_path / "config.toml")
    monkeypatch.chdir(tmp_path)
    return AppController()


def _enable(controller: AppController, hours: int = 6, **kwargs) -> None:
    apply_automation_to_config(
        default_config_path(),
        enabled=True,
        interval_hours=hours,
        ai_summary=kwargs.get("ai_summary", False),
        live_preview=kwargs.get("live_preview", False),
    )


def test_a_fresh_install_has_no_timer_running(monkeypatch, tmp_path) -> None:
    """Fail closed: installing the app must not start reading the account."""
    controller = _controller(monkeypatch, tmp_path)

    assert controller.automation["enabled"] is False
    assert controller._automation_timer.isActive() is False


def test_saving_starts_and_stops_the_timer(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)

    controller.saveAutomation(True, "6", False, False)
    assert controller._automation_timer.isActive() is True
    assert controller._automation_timer.interval() == 6 * 3600 * 1000

    controller.saveAutomation(False, "6", False, False)
    assert controller._automation_timer.isActive() is False


def test_changing_the_interval_restarts_rather_than_waiting_out_the_old_one(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.saveAutomation(True, "24", False, False)

    controller.saveAutomation(True, "2", False, False)

    assert controller._automation_timer.interval() == 2 * 3600 * 1000
    assert controller._automation_timer.isActive() is True


def test_a_tick_does_nothing_while_automation_is_off(monkeypatch, tmp_path) -> None:
    """The timer is stopped, but a stray call must be inert too."""
    controller = _controller(monkeypatch, tmp_path)
    started: list[tuple] = []
    monkeypatch.setattr(controller, "_start_analysis", lambda *a, **k: started.append((a, k)))

    controller.runAutomaticAnalysis()

    assert started == []


def test_a_tick_is_skipped_while_something_is_already_running(monkeypatch, tmp_path) -> None:
    """Queueing analyses helps nobody; the next tick will come around."""
    controller = _controller(monkeypatch, tmp_path)
    _enable(controller)
    controller._busy = True
    started: list[tuple] = []
    monkeypatch.setattr(controller, "_start_analysis", lambda *a, **k: started.append((a, k)))

    controller.runAutomaticAnalysis()

    assert started == []


def test_a_scheduled_run_is_read_only_and_does_not_move_the_user(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    _enable(controller, ai_summary=True, live_preview=True)
    captured: dict = {}

    def capture(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(controller, "_start_analysis", capture)

    controller.runAutomaticAnalysis()

    data_mode, ai_summary, ai_proposals, live_preview = captured["args"]
    assert data_mode == "REAL"
    assert ai_summary is True
    assert live_preview is True
    # AI proposals stay off: an unattended run should ask for as little as it can.
    assert ai_proposals is False
    # Negative page means "leave them where they are".
    assert captured["kwargs"]["result_page"] == -1
    # Nothing that could authorise a submission is passed at all.
    for forbidden in ("live_submit", "live_confirm", "oco_submit", "oco_confirm",
                      "earn_redeem_submit", "earn_redeem_confirm"):
        assert forbidden not in captured["kwargs"], f"{forbidden} reached a scheduled run"


def test_the_settings_the_user_saved_are_what_the_run_uses(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.saveAutomation(True, "3", True, False)
    captured: dict = {}
    monkeypatch.setattr(controller, "_start_analysis", lambda *a, **k: captured.update(args=a))

    controller.runAutomaticAnalysis()

    _, ai_summary, _, live_preview = captured["args"]
    assert ai_summary is True
    assert live_preview is False


def test_an_out_of_range_interval_is_clamped_before_it_reaches_the_timer(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)

    controller.saveAutomation(True, "0", False, False)

    assert controller._automation_timer.interval() == 1 * 3600 * 1000


def test_saving_the_same_schedule_twice_says_nothing_changed(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    notes: list[str] = []
    controller.notificationRequested.connect(notes.append)

    controller.saveAutomation(True, "6", False, False)
    controller.saveAutomation(True, "6", False, False)

    assert "Naplánovaná analýza je zapnutá" in notes[0]
    assert "Nic se nezměnilo" in notes[-1]
