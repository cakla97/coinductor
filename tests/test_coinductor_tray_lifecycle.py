"""Closing the window must end the process unless the tray is holding it.

A regression found by an installer, not by a test: quitOnLastWindowClosed was
set False once at startup rather than tracked against the tray, so with
automation off every close left an invisible process - no window, no tray icon,
holding the executable an installer wanted to replace.
"""

import shutil
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from coinductor.controller import AppController

TEMPLATE = Path(__file__).resolve().parents[1] / "config.example.toml"


@pytest.fixture(autouse=True)
def _qt_application():
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])


def _controller(monkeypatch, tmp_path) -> AppController:
    shutil.copy(TEMPLATE, tmp_path / "config.toml")
    monkeypatch.chdir(tmp_path)
    return AppController()


def test_the_tray_visibility_signal_follows_the_schedule(monkeypatch, tmp_path) -> None:
    """desktop.py drives quitOnLastWindowClosed from this, so it is the hinge."""
    controller = _controller(monkeypatch, tmp_path)
    seen: list[bool] = []
    controller.trayVisibilityRequested.connect(seen.append)

    controller.refreshTrayVisibility()
    assert seen[-1] is False, "a fresh install must quit when its window closes"

    controller.saveAutomation(True, "6", False, False)
    assert seen[-1] is True, "with a schedule the tray holds the process"

    controller.saveAutomation(False, "6", False, False)
    assert seen[-1] is False, "turning the schedule off must restore quitting"


def test_hiding_to_the_tray_says_the_app_is_still_running(monkeypatch, tmp_path) -> None:
    """An app that keeps running after you closed it has to say so."""
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    messages: list[tuple[str, str]] = []
    controller.trayMessageRequested.connect(lambda title, body: messages.append((title, body)))

    controller.announceTrayHide()

    title, body = messages[-1]
    assert "běží dál" in title
    assert "Ukončit" in body, "it must say how to stop it"
    assert "instalátorem" in body, "and why that matters"


def test_the_announcement_is_in_the_readers_language(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("en")
    messages: list[tuple[str, str]] = []
    controller.trayMessageRequested.connect(lambda title, body: messages.append((title, body)))

    controller.announceTrayHide()

    assert "still running" in messages[-1][0]


def test_desktop_ties_the_quit_flag_to_the_tray_rather_than_setting_it_once() -> None:
    """Read from the source: the bug was a single unconditional call.

    A behavioural test would need a real event loop and a real window manager;
    what actually regressed is one line, and this is the line.
    """
    source = (Path(__file__).resolve().parents[1] / "coinductor" / "desktop.py").read_text(
        encoding="utf-8"
    )
    assert "setQuitOnLastWindowClosed(not visible)" in source
    assert "setQuitOnLastWindowClosed(False)" not in source, "set once again"
