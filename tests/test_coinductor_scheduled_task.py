"""Registering the Windows scheduled task.

Every test drives schtasks through a fake, because a test that really creates a
scheduled task on the machine running it would be a test that leaves something
behind when it fails.
"""

import subprocess
import sys

import pytest

from coinductor import scheduled_task
from coinductor.scheduled_task import (
    TASK_NAME,
    executable_command,
    is_valid_time,
    query_task,
    register_task,
    remove_task,
)


class _Fake:
    """Records the argv it was asked to run and returns a canned result."""

    def __init__(self, returncode: int = 0, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.calls: list[list[str]] = []

    def __call__(self, argv, **kwargs):
        self.calls.append(list(argv))
        return subprocess.CompletedProcess(argv, self.returncode, self.stdout, "")


@pytest.fixture(autouse=True)
def _windows(monkeypatch):
    """These paths are Windows-only; CI runs a Linux leg too."""
    monkeypatch.setattr(sys, "platform", "win32")


def test_a_bad_time_is_refused_rather_than_corrected(monkeypatch) -> None:
    """A mistyped time silently becoming 00:00 would run at the worst hour."""
    fake = _Fake()
    monkeypatch.setattr(subprocess, "run", fake)

    for bad in ("", "9:00", "25:00", "07:60", "seven", "07-00", "0700"):
        ok, reason = register_task(bad)
        assert ok is False, f"{bad!r} was accepted"
        assert reason == "task_bad_time"

    assert fake.calls == [], "schtasks was called with a time that is not one"


def test_a_good_time_is_registered_daily_as_the_signed_in_user(monkeypatch) -> None:
    fake = _Fake()
    monkeypatch.setattr(subprocess, "run", fake)

    ok, reason = register_task("07:30")

    assert ok is True
    assert reason == "task_registered"
    argv = fake.calls[0]
    assert argv[:2] == ["schtasks", "/create"]
    assert "/f" in argv, "without /f a second save fails instead of replacing"
    assert TASK_NAME in argv
    assert "daily" in argv
    assert "07:30" in argv
    # Nothing here needs administrator rights, and asking for them would be a
    # much bigger promise than reading a portfolio.
    assert "/ru" not in argv and "/rl" not in argv


def test_the_registered_command_runs_this_app_read_only(monkeypatch) -> None:
    fake = _Fake()
    monkeypatch.setattr(subprocess, "run", fake)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Program Files\Coinductor\Coinductor.exe")

    register_task("07:30")

    command = fake.calls[0][fake.calls[0].index("/tr") + 1]
    assert "Coinductor.exe" in command
    assert "--run-once" in command, "the flag is what makes it headless and read-only"


def test_from_source_the_command_points_at_the_package(monkeypatch) -> None:
    """A developer's task must behave like a user's, not silently do nothing."""
    monkeypatch.delattr(sys, "frozen", raising=False)

    command = executable_command()

    assert "--run-once" in command
    assert "coinductor.desktop" in command


def test_a_failing_schtasks_is_reported_not_assumed_to_have_worked(monkeypatch) -> None:
    monkeypatch.setattr(subprocess, "run", _Fake(returncode=1))

    ok, reason = register_task("07:30")

    assert ok is False
    assert reason == "task_failed"


def test_schtasks_being_absent_does_not_raise(monkeypatch) -> None:
    def explode(*args, **kwargs):
        raise FileNotFoundError("schtasks")

    monkeypatch.setattr(subprocess, "run", explode)

    ok, reason = register_task("07:30")

    assert ok is False
    assert reason.startswith("task_failed")


def test_removal_reports_whether_there_was_anything_to_remove(monkeypatch) -> None:
    monkeypatch.setattr(subprocess, "run", _Fake(returncode=0))
    assert remove_task() == (True, "task_removed")

    monkeypatch.setattr(subprocess, "run", _Fake(returncode=1))
    assert remove_task() == (False, "task_not_registered")


def test_the_task_is_queried_by_its_own_name(monkeypatch) -> None:
    fake = _Fake(returncode=0, stdout="Coinductor scheduled analysis  Ready")
    monkeypatch.setattr(subprocess, "run", fake)

    state = query_task()

    assert state.registered is True
    assert TASK_NAME in fake.calls[0]


def test_a_missing_task_reads_as_not_registered(monkeypatch) -> None:
    monkeypatch.setattr(subprocess, "run", _Fake(returncode=1))

    assert query_task().registered is False


def test_nothing_is_attempted_off_windows(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    fake = _Fake()
    monkeypatch.setattr(subprocess, "run", fake)

    assert register_task("07:30") == (False, "task_not_windows")
    assert remove_task() == (False, "task_not_windows")
    assert query_task().registered is False
    assert fake.calls == []
    assert scheduled_task.is_supported() is False


def test_valid_times_are_the_ones_schtasks_accepts() -> None:
    assert is_valid_time("00:00") is True
    assert is_valid_time("23:59") is True
    assert is_valid_time("07:30") is True
    assert is_valid_time(" 07:30 ") is True
    assert is_valid_time("24:00") is False


def test_a_missed_run_is_caught_up_rather_than_skipped(monkeypatch) -> None:
    """StartWhenAvailable is an XML setting with no schtasks flag, and it
    defaults to false - verified on a real task, not assumed. Without it a
    machine that was off at 07:30 silently skips that day."""
    calls: list[list[str]] = []

    def fake(argv, **kwargs):
        calls.append(list(argv))
        if "/xml" in argv and "/query" in argv:
            return subprocess.CompletedProcess(
                argv, 0, "<Task><Settings><Enabled>true</Enabled></Settings></Task>", ""
            )
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake)

    ok, _ = register_task("07:30")

    assert ok is True
    reimport = [c for c in calls if "/xml" in c and "/create" in c]
    assert reimport, "the task was never re-imported with the catch-up setting"


def test_a_failed_catch_up_does_not_undo_a_working_task(monkeypatch) -> None:
    """The task still exists and still runs on time, so this is best effort."""
    def fake(argv, **kwargs):
        if "/xml" in argv:
            return subprocess.CompletedProcess(argv, 1, "", "nope")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake)

    assert register_task("07:30") == (True, "task_registered")


def test_the_next_run_and_status_are_parsed_for_the_screen() -> None:
    """Shown in the app so nobody needs a terminal to see what they scheduled.

    The labels are localised, so matching is on a stem rather than the whole
    English phrase.
    """
    from coinductor.scheduled_task import parse_task_details

    english = r"""
    TaskName:      \Coinductor scheduled analysis
    Next Run Time: 02.08.2026 7:30:00
    Status:        Ready
    """
    next_run, status = parse_task_details(english)
    assert next_run == "02.08.2026 7:30:00"
    assert status == "Ready"


def test_details_missing_from_the_output_read_as_empty() -> None:
    from coinductor.scheduled_task import parse_task_details

    assert parse_task_details("") == ("", "")
    assert parse_task_details("nothing useful here") == ("", "")
