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
from dataclasses import dataclass
from pathlib import Path

TASK_NAME = "Coinductor scheduled analysis"

# schtasks wants HH:MM. Anything else is refused rather than corrected: a
# mistyped time that silently became 00:00 would run at the worst hour.
_TIME = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


@dataclass(frozen=True)
class TaskState:
    registered: bool
    detail: str = ""

    @property
    def supported(self) -> bool:
        return sys.platform == "win32"


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
            ["schtasks", "/query", "/tn", TASK_NAME],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=_no_window(),
        )
    except Exception as exc:  # noqa: BLE001
        return TaskState(False, type(exc).__name__)
    return TaskState(completed.returncode == 0, completed.stdout.strip()[:200])


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
    return True, "task_registered"


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
