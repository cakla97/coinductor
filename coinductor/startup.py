"""Starting Coinductor when Windows signs the user in.

The in-app timer covers "while the window is open" and the scheduled task
covers one run a day with the app closed. Neither helps the person who turns
the machine on and forgets to launch anything, which is most people most days.

Registered in ``HKCU\\...\\CurrentVersion\\Run`` rather than as a logon task or
a Startup-folder shortcut. Per-user and no admin, matching how the app
installs - and, more importantly, it is the list Windows itself shows under
Task Manager's *Startup apps*, so someone can see and disable it without this
app's help. That is the same reason the daily run uses ``schtasks``: a user
who has uninstalled Coinductor should still be able to find what it left.

It starts **into the tray, not into a window**. A window appearing at every
logon is noise, and the reason to start at all is that the schedule should be
running - which needs a process, not a screen. ``--tray`` is what asks for
that, and desktop.py refuses to hide the window unless a tray icon is actually
going to be there to bring it back.
"""

from __future__ import annotations

import sys
from pathlib import Path

VALUE_NAME = "Coinductor"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# Asks the app to start hidden. Only honoured when the tray icon will be
# visible, so this can never produce a process with no way back to it.
TRAY_FLAG = "--tray"


def is_supported() -> bool:
    """Windows only. Elsewhere this whole idea belongs to the desktop session."""
    return sys.platform == "win32"


def startup_command() -> str:
    """What Windows should run at logon.

    Frozen: the shipped exe with the flag. From source: the interpreter and the
    module, so a developer's autostart behaves like a user's rather than
    silently doing nothing.
    """
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" {TRAY_FLAG}'
    module_root = Path(__file__).resolve().parents[1]
    return f'cmd /c "cd /d {module_root} && "{sys.executable}" -m coinductor.desktop {TRAY_FLAG}"'


def is_enabled() -> bool:
    """Whether the Run entry exists. False on any error: absent means off."""
    if not is_supported():
        return False
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, VALUE_NAME)
            return bool(str(value).strip())
    except FileNotFoundError:
        return False
    except Exception:  # noqa: BLE001 - an unreadable key is not an enabled one
        return False


def enable() -> tuple[bool, str]:
    """Create or refresh the Run entry. Returns (ok, reason-key).

    Rewritten rather than left alone when it already exists, because the path
    it points at changes when the app is reinstalled somewhere else, and a
    stale entry fails silently at logon - the one place nobody is watching.
    """
    if not is_supported():
        return False, "startup_not_windows"
    try:
        import winreg

        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, startup_command())
    except Exception as exc:  # noqa: BLE001
        return False, f"startup_failed:{type(exc).__name__}"
    return True, "startup_enabled"


def disable() -> tuple[bool, str]:
    """Remove the Run entry. Missing counts as success - the goal is reached."""
    if not is_supported():
        return False, "startup_not_windows"
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, VALUE_NAME)
    except FileNotFoundError:
        return True, "startup_disabled"
    except Exception as exc:  # noqa: BLE001
        return False, f"startup_failed:{type(exc).__name__}"
    return True, "startup_disabled"


def wants_tray_start(argv: list[str] | None = None) -> bool:
    """Whether this launch asked to start hidden."""
    return TRAY_FLAG in (sys.argv[1:] if argv is None else argv)
