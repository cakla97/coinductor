"""One window per set of local data.

The bug this guards against is not cosmetic. A second instance brings a second
schedule, a second listing watch and a second writer for one journal - and any
cap the app enforces per run or per window gets enforced once per process.
"""

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from coinductor.single_instance import SingleInstanceGuard, instance_key


@pytest.fixture(autouse=True)
def _qt_application():
    """QLocalServer needs an application to own its socket notifiers."""
    from PySide6.QtCore import QCoreApplication

    QCoreApplication.instance() or QCoreApplication([])


@pytest.fixture
def key(tmp_path) -> str:
    """A name of this test's own, so a real Coinductor cannot collide."""
    return instance_key(tmp_path)


def test_the_first_instance_acquires(key) -> None:
    guard = SingleInstanceGuard(key)
    try:
        assert guard.acquire() is True
    finally:
        guard.release()


def test_a_second_instance_does_not_acquire(key) -> None:
    first = SingleInstanceGuard(key)
    second = SingleInstanceGuard(key)
    try:
        assert first.acquire() is True
        assert second.acquire() is False
    finally:
        second.release()
        first.release()


def test_the_second_instance_hands_the_request_to_the_first(key) -> None:
    """The whole point: the shortcut click has to produce a window."""
    first = SingleInstanceGuard(key)
    shown: list[str] = []
    try:
        assert first.acquire() is True
        first.on_activate(lambda: shown.append("shown"))

        assert SingleInstanceGuard(key).acquire() is False
        _drain(until=lambda: bool(shown))

        assert shown == ["shown"]
    finally:
        first.release()


def test_a_request_arriving_before_the_window_exists_is_replayed(key) -> None:
    """Start-up is exactly when a second launch is most likely.

    The name is claimed before the QML engine is built, so a request can land
    while there is still nothing to show. Dropping it would leave the user who
    double-clicked the icon with no window and no explanation.
    """
    first = SingleInstanceGuard(key)
    shown: list[str] = []
    try:
        assert first.acquire() is True
        assert SingleInstanceGuard(key).acquire() is False
        # Long enough for the request to have been delivered and held, not so
        # long that proving a negative costs the suite two seconds.
        _drain(timeout_ms=300)
        assert shown == []

        first.on_activate(lambda: shown.append("shown"))

        assert shown == ["shown"]
    finally:
        first.release()


def test_releasing_lets_the_next_instance_acquire(key) -> None:
    first = SingleInstanceGuard(key)
    first.acquire()
    first.release()

    second = SingleInstanceGuard(key)
    try:
        assert second.acquire() is True
    finally:
        second.release()


def test_signalling_with_nobody_listening_is_false_not_an_error(key) -> None:
    assert SingleInstanceGuard(key).signal_existing() is False


def test_release_is_idempotent(key) -> None:
    guard = SingleInstanceGuard(key)
    guard.acquire()
    guard.release()
    guard.release()


def test_different_data_directories_do_not_block_each_other(tmp_path) -> None:
    """They share no journal and no config, so neither may refuse the other."""
    one = SingleInstanceGuard(instance_key(tmp_path / "a"))
    two = SingleInstanceGuard(instance_key(tmp_path / "b"))
    try:
        assert one.acquire() is True
        assert two.acquire() is True
    finally:
        one.release()
        two.release()


def test_the_same_data_directory_is_the_same_key(tmp_path) -> None:
    assert instance_key(tmp_path) == instance_key(str(tmp_path))


def test_a_key_is_a_usable_pipe_name(tmp_path) -> None:
    """Hashed because a path has separators and a pipe name has a length cap."""
    name = instance_key(tmp_path / "a directory with spaces")

    assert name.startswith("coinductor-")
    assert len(name) < 64
    assert "/" not in name and "\\" not in name


def test_no_data_directory_falls_back_to_the_working_directory(monkeypatch, tmp_path) -> None:
    """A source checkout has no data dir; the cwd is what it actually uses."""
    monkeypatch.chdir(tmp_path)

    assert instance_key(None) == instance_key(Path.cwd())


def _drain(until=None, timeout_ms: int = 2000) -> None:
    """Let the server see the connection the client just made.

    Delivery is asynchronous by design - the server reads on readyRead rather
    than blocking the client inside the accept - so a test that asserts
    immediately after connecting asserts too early.
    """
    from PySide6.QtCore import QCoreApplication, QDeadlineTimer

    deadline = QDeadlineTimer(timeout_ms)
    while not deadline.hasExpired():
        QCoreApplication.processEvents()
        if until is not None and until():
            return
