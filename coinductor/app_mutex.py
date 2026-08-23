"""A named mutex, held for as long as Coinductor runs.

Nothing in the application reads it. It exists so that the *installer* can tell
the program is running: Inno Setup's `AppMutex` opens this name before it writes
anything, and refuses to continue while it is held.

That is a different question from the one `single_instance.py` answers. The
QLocalServer guard asks "is a window already open for this data folder", and is
per-folder on purpose - two data folders are two independent Coinductors. The
installer's question is "is *any* copy of this program running", because any of
them holds the files it is about to replace. So this is deliberately global to
the user's session and takes no notice of the data directory.

Why it matters: `CloseApplications=yes` alone did not stop an upgrade landing on
top of a running program. Files the running process still had open were left as
they were, and the install ended up a mixture - new data files over an older
binary - which then failed in ways that looked nothing like a bad install.

Failing to create the mutex is not an error. The worst case is the situation we
already had, and refusing to start a trading application because Windows would
not hand out a synchronisation object would be a far worse trade.
"""

from __future__ import annotations

import sys

# Tied to the installer's AppId so the two cannot drift into different names
# without somebody noticing that they no longer look alike. A test holds
# packaging/coinductor.iss to this string.
MUTEX_NAME = "Coinductor-6F3B9C24-8A1E-4C7D-9E2F-1A5B7C3D8E90"

_handle: int | None = None


def acquire(name: str = MUTEX_NAME) -> bool:
    """Create the mutex and keep it for the life of the process.

    Returns whether a handle is now held. Already holding one is a success:
    the point is that the name exists, not that we were first to make it.
    """
    global _handle
    if _handle is not None:
        return True
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        # The handle is never closed. It is released when the process ends,
        # which is exactly the moment the installer may safely proceed.
        handle = ctypes.windll.kernel32.CreateMutexW(None, False, name)
    except Exception:
        return False
    if not handle:
        return False
    _handle = handle
    return True


def held() -> bool:
    return _handle is not None
