from __future__ import annotations

import os
from pathlib import Path
import sys

from .paths import bootstrap_data_dir, resolve_data_dir

# Qt is imported inside main() rather than here. A scheduled run has no window,
# no display and no reason to load a GUI toolkit, and on a session without a
# desktop importing one is not merely wasteful - it can fail.


def run_once() -> int:
    """One analysis, no window, then exit. What the scheduled task calls.

    The shipped build is a single windowed executable - there is no `python -m
    trading_agent` inside it - so the scheduled task runs this same binary with
    a flag rather than a second entry point that would have to be bundled,
    signed and kept in step.

    Read-only by construction: RuntimeFlags are left at their defaults, which
    fail closed, and no confirmation string exists to pass. Needs no Qt at all.
    """
    from .application import CoinductorApplication
    from .models import RunOptions
    from .automation import read_automation
    from trading_agent.config import default_config_path

    settings = read_automation(default_config_path())
    try:
        result = CoinductorApplication().run_analysis(
            RunOptions(
                data_mode="REAL",
                ai_summary=settings.ai_summary,
                ai_proposals=False,
                live_preview=settings.live_preview,
            )
        )
    except Exception as exc:  # noqa: BLE001 - a scheduled run reports, never crashes
        print(f"Coinductor scheduled run failed: {exc}")
        return 1
    print(f"Run {result.run_id} finished: {result.status} - {result.decision}")
    return 0


def main() -> int:
    data_dir = resolve_data_dir()
    if data_dir is not None:
        bootstrap_data_dir(data_dir)
        os.chdir(data_dir)

    if "--run-once" in sys.argv[1:]:
        return run_once()

    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QIcon
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtWidgets import QApplication

    from .app_mutex import acquire as hold_app_mutex
    from .controller import AppController
    from .single_instance import SingleInstanceGuard, instance_key
    from .startup import wants_tray_start
    from .tray import CoinductorTray

    # QApplication rather than QGuiApplication: QSystemTrayIcon lives in
    # QtWidgets and refuses to work under the lighter one. It is a subclass, so
    # nothing about the QML side changes.
    app = QApplication(sys.argv)
    app.setApplicationName("Coinductor")
    app.setOrganizationName("Coinductor")
    icon_path = Path(__file__).parent / "coinductor.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Before the engine, the controller or the schedule: a second launch should
    # cost a pipe round trip and exit, not build all of that and throw it away.
    # The tray menu could always find the running app because it lives inside
    # it; until this, the desktop shortcut could not, and started a rival.
    # Before anything is opened: the installer asks whether this name exists,
    # and the answer has to be yes for every copy that is running, including one
    # about to exit as a duplicate. Answers a different question from the guard
    # below - see app_mutex.py - and its failure is never fatal.
    hold_app_mutex()

    guard = SingleInstanceGuard(instance_key(data_dir))
    if not guard.acquire():
        return 0
    app.aboutToQuit.connect(guard.release)

    engine = QQmlApplicationEngine()
    controller = AppController(engine)
    engine.rootContext().setContextProperty("appController", controller)
    qml_path = Path(__file__).parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path.resolve())))
    if not engine.rootObjects():
        return 1

    tray = CoinductorTray(controller, icon_path)
    # Launching again is a request to see the window, which is exactly what the
    # tray's Open does - so it is the same call, not a parallel one.
    guard.on_activate(tray.show_window)

    def follow_tray(visible: bool) -> None:
        if visible:
            tray.show()
        else:
            tray.hide()
        # Tied to the tray, never set once. Closing the last window normally
        # ends the process; with the tray active the window is hidden instead,
        # so quitting then would defeat the point. Setting it False
        # unconditionally left an invisible process with no window and no tray
        # icon behind every close - which is also why an installer could not
        # replace a "closed" Coinductor.
        app.setQuitOnLastWindowClosed(not visible)

    controller.trayVisibilityRequested.connect(follow_tray)
    controller.wizardLanguageChanged.connect(tray.retranslate)
    controller.refreshTrayVisibility()

    # A logon start wants the schedule running, not a window in the way. Only
    # honoured when a tray icon is actually going to be there: hiding without
    # one leaves a process the user can neither see nor stop, which is the
    # exact failure follow_tray exists to avoid. Without the tray the window
    # simply opens, which is a visible wrong answer rather than an invisible
    # one.
    if wants_tray_start() and controller.keepRunningInTray and CoinductorTray.available():
        engine.rootObjects()[0].hide()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
