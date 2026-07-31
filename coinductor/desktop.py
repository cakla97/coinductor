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

    from .controller import AppController
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

    engine = QQmlApplicationEngine()
    controller = AppController(engine)
    engine.rootContext().setContextProperty("appController", controller)
    qml_path = Path(__file__).parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path.resolve())))
    if not engine.rootObjects():
        return 1

    tray = CoinductorTray(controller, icon_path)
    controller.trayVisibilityRequested.connect(
        lambda visible: tray.show() if visible else tray.hide()
    )
    controller.wizardLanguageChanged.connect(tray.retranslate)
    # Closing the last window normally ends the process. With the tray active
    # the window is hidden rather than closed, so this has to be off or the app
    # would exit the moment it went to the tray.
    app.setQuitOnLastWindowClosed(False)
    controller.refreshTrayVisibility()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
