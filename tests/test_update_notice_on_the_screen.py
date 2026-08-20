"""The update notice, as the controller and the screen see it.

The regression this file exists for: the first wiring read the config directly
instead of going through `read_check_on_start`, so the offline guard did not
reach it and building a controller sent the whole test suite to github.com -
which crashed the run outright. A controller must never reach the network by
being constructed.
"""

import shutil
from pathlib import Path

import pytest

from coinductor.update_check import DISABLE_ENV, UpdateCheckService

TEMPLATE = Path(__file__).resolve().parents[1] / "config.example.toml"

pytest.importorskip("PySide6")

from coinductor.controller import AppController  # noqa: E402


@pytest.fixture
def controller(monkeypatch, tmp_path) -> "AppController":
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])
    shutil.copy(TEMPLATE, tmp_path / "config.toml")
    monkeypatch.chdir(tmp_path)
    return AppController()


def test_building_a_controller_reaches_no_network(monkeypatch, tmp_path) -> None:
    """The guard has to reach the controller, not only the settings property."""
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])
    calls = []
    monkeypatch.setattr(
        UpdateCheckService, "fetch", lambda self: calls.append("asked") or ""
    )
    shutil.copy(TEMPLATE, tmp_path / "config.toml")
    monkeypatch.chdir(tmp_path)

    AppController()

    assert calls == []


def test_nothing_is_announced_without_a_recorded_release(controller) -> None:
    assert controller.updateInfo["available"] is False


def test_a_recorded_release_is_announced(controller, tmp_path) -> None:
    controller._update_check.record("v99.0.0")

    info = controller.updateInfo

    assert info["available"] is True
    assert info["version"] == "v99.0.0"
    assert info["url"].startswith("https://github.com/")


def test_the_current_version_is_shown_next_to_it(controller) -> None:
    """So the line says what you have, not only what exists."""
    from trading_agent import __version__

    assert controller.updateInfo["current"] == f"v{__version__}"


def test_dismissing_puts_it_away(controller) -> None:
    controller._update_check.record("v99.0.0")

    controller.dismissUpdateNotice()

    assert controller.updateInfo["available"] is False


def test_a_later_release_speaks_up_after_a_dismissal(controller) -> None:
    controller._update_check.record("v99.0.0")
    controller.dismissUpdateNotice()

    controller._update_check.record("v99.1.0")

    assert controller.updateInfo["available"] is True


def test_the_settings_switch_reads_and_writes_the_config(controller, monkeypatch) -> None:
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    assert controller.updateCheckEnabled is True

    controller.setUpdateCheckEnabled(False)

    assert controller.updateCheckEnabled is False


def test_turning_the_switch_off_stops_the_check(controller, monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        UpdateCheckService, "fetch", lambda self: calls.append("asked") or ""
    )
    controller.setUpdateCheckEnabled(False)

    controller._start_update_check()

    assert calls == []
