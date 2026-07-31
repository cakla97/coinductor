"""The listing watcher as the controller drives it.

Two things matter beyond "does it run": the watcher must never reach a submit
path, and saving one half of the automation settings must not silently reset
the other - the schedule panel and the listing panel are different screens.
"""

import shutil
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from coinductor.automation import read_automation
from coinductor.controller import AppController
from coinductor.listing_watcher import ListingScan
from trading_agent.config import default_config_path

TEMPLATE = Path(__file__).resolve().parents[1] / "config.example.toml"


@pytest.fixture(autouse=True)
def _qt_application():
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])


def _controller(monkeypatch, tmp_path) -> AppController:
    shutil.copy(TEMPLATE, tmp_path / "config.toml")
    monkeypatch.chdir(tmp_path)
    return AppController()


def test_a_fresh_install_is_not_watching(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)

    assert read_automation(default_config_path()).watch_listings is False
    assert controller._listing_timer.isActive() is False


def test_turning_the_watch_on_starts_the_timer(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)

    controller.saveListingWatch(True, "15")

    assert controller._listing_timer.isActive() is True
    assert controller._listing_timer.interval() == 15 * 60 * 1000

    controller.saveListingWatch(False, "15")
    assert controller._listing_timer.isActive() is False


def test_the_listing_interval_is_clamped(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)

    controller.saveListingWatch(True, "1")

    assert controller._listing_timer.interval() == 5 * 60 * 1000


def test_saving_the_listing_watch_leaves_the_analysis_schedule_alone(monkeypatch, tmp_path) -> None:
    """Two panels, one config section. Neither may quietly undo the other."""
    controller = _controller(monkeypatch, tmp_path)
    controller.saveAutomation(True, "8", False, True)

    controller.saveListingWatch(True, "20")

    settings = read_automation(default_config_path())
    assert settings.enabled is True
    assert settings.interval_hours == 8
    assert settings.live_preview is True
    assert settings.watch_listings is True
    assert settings.listing_interval_minutes == 20


def test_saving_the_analysis_schedule_leaves_the_listing_watch_alone(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.saveListingWatch(True, "20")

    controller.saveAutomation(True, "8", False, False)

    settings = read_automation(default_config_path())
    assert settings.watch_listings is True
    assert settings.listing_interval_minutes == 20


def test_a_scan_is_not_started_while_the_watch_is_off(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    started: list[int] = []
    monkeypatch.setattr(controller, "_start_worker", lambda *a, **k: started.append(1))

    controller.scanListings()

    assert started == []


def test_a_new_listing_notifies_and_says_nothing_was_bought(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    notes: list[str] = []
    tray: list[tuple] = []
    controller.notificationRequested.connect(notes.append)
    controller.trayMessageRequested.connect(lambda t, b: tray.append((t, b)))

    controller._on_listing_scan_completed(
        ListingScan(({"symbol": "NEWUSDC", "baseAsset": "NEW"},), total_known=42)
    )

    assert "NEWUSDC" in notes[-1]
    assert "nic nekoupil" in notes[-1], "the notification must say it did not act"
    assert tray and "NEWUSDC" in tray[-1][1]


def test_a_scan_that_found_nothing_does_not_notify(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    notes: list[str] = []
    controller.notificationRequested.connect(notes.append)

    controller._on_listing_scan_completed(ListingScan((), total_known=42))

    assert notes == []
    assert "42" in controller.listingStatus


def test_an_outage_is_reported_rather_than_swallowed(monkeypatch, tmp_path) -> None:
    """A watcher silently failing for a week is worse than one that says so."""
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("en")

    controller._on_listing_scan_completed(ListingScan((), total_known=0, error="503"))

    assert "503" in controller.listingStatus
    assert "Could not reach Binance" in controller.listingStatus


def test_adding_a_listing_makes_it_analysable_and_says_nothing_was_bought(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    notes: list[str] = []
    controller.notificationRequested.connect(notes.append)

    controller.addAllowedSymbol("newusdc")

    from coinductor.allowed_symbols import read_allowed_symbols

    assert "NEWUSDC" in read_allowed_symbols(default_config_path())
    assert "NEWUSDC" in notes[-1]
    assert "Nic se nekoupilo" in notes[-1]
    # The override list the guarded flow checks against is refreshed, or the
    # pair would be eligible in the config and refused by the running app.
    assert "NEWUSDC" in controller.manualOverrideSymbols


def test_adding_nonsense_changes_nothing_and_says_why(monkeypatch, tmp_path) -> None:
    controller = _controller(monkeypatch, tmp_path)
    controller.setWizardLanguage("cs")
    notes: list[str] = []
    controller.notificationRequested.connect(notes.append)

    from coinductor.allowed_symbols import read_allowed_symbols

    before = read_allowed_symbols(default_config_path())
    controller.addAllowedSymbol("not a pair")

    assert read_allowed_symbols(default_config_path()) == before
    assert "nevypadá jako pár" in notes[-1]


def test_the_watcher_never_touches_a_submit_path(monkeypatch, tmp_path) -> None:
    """The strongest statement available: it starts no analysis at all."""
    controller = _controller(monkeypatch, tmp_path)
    started: list = []
    monkeypatch.setattr(controller, "_start_analysis", lambda *a, **k: started.append(k))

    controller.saveListingWatch(True, "15")
    controller._on_listing_scan_completed(
        ListingScan(({"symbol": "NEWUSDC"},), total_known=1)
    )
    controller.addAllowedSymbol("NEWUSDC")

    assert started == []
