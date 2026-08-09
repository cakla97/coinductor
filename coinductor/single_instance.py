"""One Coinductor per set of local data, however it was launched.

The tray menu's *Open Coinductor* always found the running app, because it is
inside it. The desktop shortcut had nothing to find it with, so a second launch
built a second everything: a second schedule, a second listing watch, and a
second writer for the same journal and the same `config.toml`. Two schedules is
the visible half. The half that matters is that anything counting against a cap
counts it once per process, so two instances quietly double every per-run and
per-window limit the app enforces.

Built on QLocalServer rather than a lock file, because detecting the other
instance is only half of what a shortcut needs. The user who double-clicked the
icon wants a window; something has to carry that request across, and a lock
file can only refuse.

**The connection is the message.** There is deliberately no payload. A second
instance connects and then exits immediately, and on Windows a QLocalSocket
that is closed - or destroyed by the process leaving - discards whatever was
written into it before the server ever accepts. This was measured, not assumed:
the write is lost with `disconnectFromServer`, lost with `waitForDisconnected`,
and arrives only if the client stays alive until the server has read it, which
is exactly what a process about to exit cannot promise. The connection itself
survives all of those, so that is what this protocol uses. Anyone tempted to
add a message here should expect it to vanish.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

from PySide6.QtNetwork import QLocalServer, QLocalSocket

# Milliseconds. Small on purpose: this sits in front of every start-up, so a
# machine where nothing is listening must reach the "no instance" answer fast.
_CONNECT_TIMEOUT_MS = 500


def instance_key(data_dir: Path | str | None) -> str:
    """A name per data directory, not per machine.

    Two builds pointing at different data directories share no journal and no
    config, so neither has any business refusing to start because the other is
    running. Hashed rather than used raw because the name becomes a pipe name,
    which has a length limit and no room for path separators.

    On Windows this doubles as the per-user split that the pipe namespace does
    not give for free: each account's data directory lives under its own
    %LOCALAPPDATA%, so each account gets its own key.
    """
    root = str(Path(data_dir).resolve()) if data_dir is not None else str(Path.cwd())
    digest = hashlib.sha1(root.casefold().encode("utf-8")).hexdigest()[:16]
    return f"coinductor-{digest}"


class SingleInstanceGuard:
    """Owns the name while this process is the one with the window."""

    def __init__(self, key: str) -> None:
        self._key = key
        self._server: QLocalServer | None = None
        self._handler: Callable[[], None] | None = None
        # A request that arrived before the window existed. Dropping it would
        # be worst exactly where this feature is used: the shortcut click that
        # is waiting for a window to appear.
        self._pending = False

    @property
    def key(self) -> str:
        return self._key

    def acquire(self) -> bool:
        """True when this process should build a window.

        False means a running instance was found *and has been asked to show
        itself*, so the caller's whole remaining job is to exit quietly.
        """
        if self.signal_existing():
            return False
        # A process killed rather than closed leaves the name behind on Unix;
        # Windows drops it with the process. Removing it is safe only because
        # signal_existing has just established that nothing answers on it.
        QLocalServer.removeServer(self._key)
        server = QLocalServer()
        if not server.listen(self._key):
            # Two shortcuts double-clicked at once. Whoever won owns the
            # window; this process hands its request over and steps aside.
            self.signal_existing()
            return False
        server.newConnection.connect(self._on_connection)
        self._server = server
        return True

    def signal_existing(self) -> bool:
        """Ask a running instance to show itself. False when there is none.

        Connecting *is* the request - see the module docstring on why there is
        nothing written into the socket. True therefore means an instance
        answered, which is also the only thing `acquire` needs to know: whoever
        took the connection owns the name, and taking the name off a live
        instance would be far worse than a click that did nothing visible.
        """
        socket = QLocalSocket()
        socket.connectToServer(self._key)
        if not socket.waitForConnected(_CONNECT_TIMEOUT_MS):
            socket.abort()
            return False
        socket.disconnectFromServer()
        return True

    def on_activate(self, handler: Callable[[], None]) -> None:
        """What to do when another launch asks for the window.

        Set once the window exists rather than at acquire time, and anything
        that arrived in between is replayed here instead of being lost.
        """
        self._handler = handler
        if self._pending:
            self._pending = False
            handler()

    def release(self) -> None:
        """Give the name up. Idempotent, so shutdown order cannot matter."""
        if self._server is not None:
            self._server.close()
            self._server = None
        QLocalServer.removeServer(self._key)

    def _on_connection(self) -> None:
        server = self._server
        if server is None:
            return
        while server.hasPendingConnections():
            socket = server.nextPendingConnection()
            socket.disconnectFromServer()
            socket.deleteLater()
            self._activate()

    def _activate(self) -> None:
        if self._handler is None:
            self._pending = True
            return
        self._handler()
