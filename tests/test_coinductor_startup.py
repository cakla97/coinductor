"""Starting Coinductor when Windows signs the user in.

The point is that the schedule survives a restart, which is the failure people
actually hit: the machine goes on and nobody remembers to launch anything.

Every test that touches the registry writes under a temporary key, never the
real ``...\\CurrentVersion\\Run`` - a test that enabled autostart on the machine
running it would be a test that leaves something behind when it fails.
"""

import sys

import pytest

from coinductor import startup


@pytest.fixture
def isolated_run_key(monkeypatch, tmp_path):
    """Point the module at a scratch key under HKCU."""
    if sys.platform != "win32":
        pytest.skip("registry autostart is Windows only")
    key = rf"Software\CoinductorTests\{tmp_path.name}\Run"
    monkeypatch.setattr(startup, "RUN_KEY", key)
    yield key
    import winreg

    for path in (key, key.rsplit("\\", 1)[0], r"Software\CoinductorTests"):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
        except OSError:
            pass


def test_it_is_off_until_asked(isolated_run_key) -> None:
    assert startup.is_enabled() is False


def test_enabling_then_disabling_round_trips(isolated_run_key) -> None:
    assert startup.enable() == (True, "startup_enabled")
    assert startup.is_enabled() is True

    assert startup.disable() == (True, "startup_disabled")
    assert startup.is_enabled() is False


def test_disabling_something_absent_is_success(isolated_run_key) -> None:
    """The goal is "does not start on its own", and it is already reached."""
    assert startup.disable() == (True, "startup_disabled")


def test_enabling_twice_refreshes_rather_than_failing(isolated_run_key) -> None:
    """The path changes when the app is reinstalled elsewhere, and a stale
    entry fails silently at logon - the one place nobody is watching."""
    startup.enable()
    monkeyed = "C:\\Elsewhere\\Coinductor.exe --tray"

    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, isolated_run_key, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, startup.VALUE_NAME, 0, winreg.REG_SZ, monkeyed)

    startup.enable()

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, isolated_run_key) as key:
        assert winreg.QueryValueEx(key, startup.VALUE_NAME)[0] != monkeyed


def test_an_empty_value_does_not_count_as_enabled(isolated_run_key) -> None:
    import winreg

    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, isolated_run_key, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, startup.VALUE_NAME, 0, winreg.REG_SZ, "   ")

    assert startup.is_enabled() is False


def test_the_command_asks_for_a_tray_start() -> None:
    """Without the flag it would open a window at every logon, which is noise."""
    assert startup.TRAY_FLAG in startup.startup_command()


def test_the_flag_is_read_from_the_command_line() -> None:
    assert startup.wants_tray_start([startup.TRAY_FLAG]) is True
    assert startup.wants_tray_start([]) is False
    assert startup.wants_tray_start(["--run-once"]) is False


def test_nothing_is_claimed_off_windows(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")

    assert startup.is_supported() is False
    assert startup.is_enabled() is False
    assert startup.enable() == (False, "startup_not_windows")


# ---------------------------------------------------------------------------
# The screen.
# ---------------------------------------------------------------------------

pytest.importorskip("PySide6")

import shutil  # noqa: E402
from pathlib import Path  # noqa: E402

from coinductor.automation import apply_automation_to_config  # noqa: E402
from coinductor.controller import AppController  # noqa: E402
from trading_agent.config import default_config_path  # noqa: E402

TEMPLATE = Path(__file__).resolve().parents[1] / "config.example.toml"


@pytest.fixture
def controller(monkeypatch, tmp_path) -> "AppController":
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication([])
    shutil.copy(TEMPLATE, tmp_path / "config.toml")
    monkeypatch.chdir(tmp_path)
    return AppController()


def test_it_is_pointless_until_a_schedule_exists(controller) -> None:
    """A background app with nothing to do is one people hunt down and kill."""
    assert controller.startOnLogon["useful"] is False


def test_turning_a_schedule_on_makes_it_useful(controller) -> None:
    apply_automation_to_config(
        default_config_path(), enabled=True, interval_hours=6, ai_summary=False, live_preview=False
    )

    assert controller.startOnLogon["useful"] is True


def test_the_screen_says_which_way_it_went(controller, monkeypatch) -> None:
    """It changes what happens at every logon; "saved" is not enough."""
    monkeypatch.setattr("coinductor.controller.enable_startup", lambda: (True, "startup_enabled"))
    monkeypatch.setattr("coinductor.controller.disable_startup", lambda: (True, "startup_disabled"))
    controller.setWizardLanguage("cs")
    notes: list[str] = []
    controller.notificationRequested.connect(notes.append)

    controller.setStartOnLogon(True)
    assert "spustí" in notes[-1]

    controller.setStartOnLogon(False)
    assert "nespustí" in notes[-1]


def test_a_refused_registry_write_is_reported(controller, monkeypatch) -> None:
    monkeypatch.setattr(
        "coinductor.controller.enable_startup", lambda: (False, "startup_failed:PermissionError")
    )
    controller.setWizardLanguage("cs")
    notes: list[str] = []
    controller.notificationRequested.connect(notes.append)

    controller.setStartOnLogon(True)

    assert "odmítly" in notes[-1]


def test_the_panel_is_on_the_automation_page() -> None:
    qml = (Path(__file__).parents[1] / "coinductor" / "qml" / "Main.qml").read_text(encoding="utf-8")

    assert 'objectName: "startupPanel"' in qml
    assert "appController.setStartOnLogon" in qml
    # Disabled without a schedule, and it says why rather than just greying out.
    assert "enabled: appController.startOnLogon.useful" in qml
    assert "startup_needs_automation" in qml


def test_the_desktop_only_hides_when_a_tray_icon_will_be_there() -> None:
    """Hiding without one leaves a process the user can neither see nor stop."""
    source = (Path(__file__).parents[1] / "coinductor" / "desktop.py").read_text(encoding="utf-8")

    assert "wants_tray_start() and controller.keepRunningInTray and CoinductorTray.available()" in source
