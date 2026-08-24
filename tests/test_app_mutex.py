"""The name the installer looks for before it writes anything.

`CloseApplications=yes` alone did not stop an upgrade landing on top of a
running Coinductor: the files it still had open were left as they were, and the
install became new data files over an older binary - which then failed in ways
that looked nothing like a bad install. The mutex is what lets Inno refuse.

The two halves live in different files and different languages, so the last test
here is the one that matters most: it holds them to the same string.
"""

import sys
from pathlib import Path

import pytest

from coinductor import app_mutex

ISS = Path(__file__).resolve().parents[1] / "packaging" / "coinductor.iss"


@pytest.fixture(autouse=True)
def _forget_any_handle(monkeypatch):
    """Each test starts having acquired nothing."""
    monkeypatch.setattr(app_mutex, "_handle", None)


def test_the_name_is_stable() -> None:
    """Changing it silently would make every installed copy invisible to Inno."""
    assert app_mutex.MUTEX_NAME == "Coinductor-6F3B9C24-8A1E-4C7D-9E2F-1A5B7C3D8E90"


def test_the_installer_looks_for_exactly_that_name() -> None:
    assert f"AppMutex={app_mutex.MUTEX_NAME}" in ISS.read_text(encoding="utf-8")


def test_the_running_app_message_says_where_to_click() -> None:
    """Inno's default says "close all instances of it now", which names nothing
    a tray-only application actually shows. Both messages have to explain the
    notification area, or the guard just blocks people without helping them."""
    text = ISS.read_text(encoding="utf-8")

    for message in ("SetupAppRunningError", "UninstallAppRunningError"):
        line = next(row for row in text.splitlines() if row.startswith(f"{message}="))
        assert "notification area" in line, message
        assert "Quit" in line, message
        assert "Task Manager" in line, message


def test_the_installer_wipes_the_previous_payload() -> None:
    """The mutex stops files being locked; this stops a locked file from the
    past outliving every future install. One without the other is not enough."""
    text = ISS.read_text(encoding="utf-8")

    assert "[InstallDelete]" in text
    assert r'Type: filesandordirs; Name: "{app}\_internal"' in text


def test_nothing_is_held_before_acquiring() -> None:
    assert app_mutex.held() is False


@pytest.mark.skipif(sys.platform != "win32", reason="named mutexes are a Windows thing")
def test_acquiring_holds_the_handle() -> None:
    assert app_mutex.acquire("Coinductor-test-acquire") is True
    assert app_mutex.held() is True


@pytest.mark.skipif(sys.platform != "win32", reason="named mutexes are a Windows thing")
def test_acquiring_twice_is_a_success_not_a_second_handle() -> None:
    """Already holding one is the desired state, so it must not read as failure."""
    app_mutex.acquire("Coinductor-test-twice")
    first = app_mutex._handle

    assert app_mutex.acquire("Coinductor-test-twice") is True
    assert app_mutex._handle == first


@pytest.mark.skipif(sys.platform != "win32", reason="named mutexes are a Windows thing")
def test_a_name_already_taken_still_counts_as_held() -> None:
    """Two Coinductors on two data folders both hold it, and both should keep
    the installer out - the installer's question is about the program, not the
    data directory."""
    import ctypes

    other = ctypes.windll.kernel32.CreateMutexW(None, False, "Coinductor-test-shared")
    try:
        assert app_mutex.acquire("Coinductor-test-shared") is True
    finally:
        ctypes.windll.kernel32.CloseHandle(other)


def test_a_refusal_from_the_os_is_not_fatal(monkeypatch) -> None:
    """Refusing to start a trading app because Windows would not hand out a
    synchronisation object is a far worse trade than the risk it covers."""
    monkeypatch.setattr(sys, "platform", "win32")

    class Boom:
        def __getattr__(self, name):
            raise OSError("no handles today")

    monkeypatch.setattr("ctypes.windll", Boom(), raising=False)

    assert app_mutex.acquire("Coinductor-test-boom") is False
    assert app_mutex.held() is False


def test_it_does_nothing_off_windows(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")

    assert app_mutex.acquire("Coinductor-test-linux") is False
