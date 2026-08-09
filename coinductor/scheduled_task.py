"""Running an analysis while Coinductor is closed, via Windows Task Scheduler.

The in-app timer covers "while the window is open"; this covers the rest. Both
end at the same wall: **the machine has to be on**. There is no server doing
this, which is the same property that means there is no account and no
telemetry, and it is stated in the UI rather than left to be discovered.

Registered through `schtasks` rather than by writing XML, because the CLI is
what a user can inspect and delete without this app's help - `schtasks /query
/tn Coinductor` tells them the truth even if Coinductor is uninstalled.

The task runs the shipped executable with --run-once. That path is read-only by
construction: RuntimeFlags fail closed and no confirmation string exists to
pass, so an unattended run cannot place an order however it is invoked.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

TASK_NAME = "Coinductor scheduled analysis"

# schtasks wants HH:MM. Anything else is refused rather than corrected: a
# mistyped time that silently became 00:00 would run at the worst hour.
_TIME = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


# The daily start out of the task's own XML. Read from there rather than from
# `/fo LIST`, because the XML schema's tag names are fixed while the LIST
# labels are localised - the same problem parse_task_details has to work
# around by matching Czech stems.
_START_BOUNDARY = re.compile(r"<StartBoundary>\s*\d{4}-\d{2}-\d{2}T(\d{2}:\d{2})")


@dataclass(frozen=True)
class TaskState:
    registered: bool
    detail: str = ""
    next_run: str = ""
    status: str = ""
    # What Windows actually has, which is not necessarily what this app last
    # registered: the task outlives the process, and can be edited in Task
    # Scheduler by someone who never opens Coinductor.
    start_time: str = ""

    @property
    def supported(self) -> bool:
        return sys.platform == "win32"


def parse_task_details(output: str) -> tuple[str, str]:
    """Next run time and status out of `schtasks /fo LIST`.

    Parsed rather than shown raw because the raw form is a wall of fields, and
    because the labels are localised - matching the value after the first colon
    on a line whose label contains a known stem works on a Czech Windows too.
    """
    next_run, status = "", ""
    for line in output.splitlines():
        if ":" not in line:
            continue
        label, _, value = line.partition(":")
        label = label.strip().lower()
        value = value.strip()
        if not value:
            continue
        if not next_run and ("next run" in label or "příští" in label or "pristi" in label):
            next_run = value
        elif not status and label.endswith("status") or label.endswith("stav"):
            status = status or value
    return next_run, status


def parse_start_time(xml: str) -> str:
    """`HH:MM` out of a task's XML definition, or empty when it has none."""
    match = _START_BOUNDARY.search(xml)
    return match.group(1) if match else ""


def is_supported() -> bool:
    """Windows only. Everywhere else the in-app timer is the whole story."""
    return sys.platform == "win32"


def is_valid_time(value: str) -> bool:
    return bool(_TIME.match(str(value).strip()))


def executable_command() -> str:
    """What the task should run.

    Frozen: the shipped exe with the flag. From source: the interpreter and the
    module, so a developer's task behaves like a user's rather than silently
    doing nothing.
    """
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --run-once'
    # From source there is no bundled exe, and schtasks sets no working
    # directory, so the interpreter is told where the package lives.
    module_root = Path(__file__).resolve().parents[1]
    return f'cmd /c "cd /d {module_root} && "{sys.executable}" -m coinductor.desktop --run-once"'


def query_task() -> TaskState:
    if not is_supported():
        return TaskState(False, "not Windows")
    try:
        completed = subprocess.run(  # noqa: S603
            ["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=_no_window(),
        )
    except Exception as exc:  # noqa: BLE001
        return TaskState(False, type(exc).__name__)
    if completed.returncode != 0:
        return TaskState(False, "")
    next_run, status = parse_task_details(completed.stdout)
    return TaskState(True, completed.stdout.strip()[:200], next_run, status, _query_start_time())


def _query_start_time() -> str:
    """The registered daily time, via a second query for the XML definition.

    Only reached once the LIST query has already established the task exists,
    so this is not a cost paid on a machine that has never registered one.
    Best effort: a panel showing the time it was last told beats a panel
    showing nothing because a subprocess had a bad day.
    """
    try:
        exported = subprocess.run(  # noqa: S603
            ["schtasks", "/query", "/tn", TASK_NAME, "/xml"],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=_no_window(),
        )
    except Exception:  # noqa: BLE001
        return ""
    return parse_start_time(exported.stdout) if exported.returncode == 0 else ""


def register_task(daily_at: str) -> tuple[bool, str]:
    """Create or replace the daily task. Returns (ok, reason-key)."""
    if not is_supported():
        return False, "task_not_windows"
    if not is_valid_time(daily_at):
        return False, "task_bad_time"
    try:
        completed = subprocess.run(  # noqa: S603
            [
                "schtasks", "/create", "/f",
                "/tn", TASK_NAME,
                "/tr", executable_command(),
                "/sc", "daily",
                "/st", daily_at.strip(),
                # Deliberately absent: /ru SYSTEM and /rl HIGHEST. This runs as
                # the signed-in user with ordinary rights, because it reads that
                # user's keychain and nothing here needs more than that.
            ],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=_no_window(),
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"task_failed:{type(exc).__name__}"
    if completed.returncode != 0:
        return False, "task_failed"
    _enable_catch_up()
    return True, "task_registered"


def _enable_catch_up() -> bool:
    """Run a missed start as soon as the machine is next on.

    schtasks has no flag for this - StartWhenAvailable is an XML setting and
    defaults to false, which was verified on a real task rather than assumed.
    Without it a machine that was off at 07:30 simply skips that day, silently,
    which is the least useful behaviour available to a daily analysis.

    Best effort: if the export/import round trip fails the task still exists and
    still runs on time, so a failure here is not worth refusing the whole thing.
    """
    try:
        exported = subprocess.run(  # noqa: S603
            ["schtasks", "/query", "/tn", TASK_NAME, "/xml"],
            capture_output=True, text=True, timeout=20, creationflags=_no_window(),
        )
        if exported.returncode != 0 or "<Settings>" not in exported.stdout:
            return False
        xml = exported.stdout
        if "<StartWhenAvailable>" in xml:
            xml = re.sub(
                r"<StartWhenAvailable>.*?</StartWhenAvailable>",
                "<StartWhenAvailable>true</StartWhenAvailable>",
                xml,
            )
        else:
            xml = xml.replace("<Settings>", "<Settings>\n    <StartWhenAvailable>true</StartWhenAvailable>", 1)
        with tempfile.NamedTemporaryFile(
            "w", suffix=".xml", delete=False, encoding="utf-16"
        ) as handle:
            handle.write(xml)
            path = handle.name
        try:
            imported = subprocess.run(  # noqa: S603
                ["schtasks", "/create", "/f", "/tn", TASK_NAME, "/xml", path],
                capture_output=True, text=True, timeout=20, creationflags=_no_window(),
            )
            return imported.returncode == 0
        finally:
            Path(path).unlink(missing_ok=True)
    except Exception:  # noqa: BLE001
        return False


def remove_task() -> tuple[bool, str]:
    if not is_supported():
        return False, "task_not_windows"
    try:
        completed = subprocess.run(  # noqa: S603
            ["schtasks", "/delete", "/f", "/tn", TASK_NAME],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=_no_window(),
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"task_failed:{type(exc).__name__}"
    if completed.returncode != 0:
        return False, "task_not_registered"
    return True, "task_removed"


def _no_window() -> int:
    """Keep schtasks from flashing a console window over the app."""
    return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
