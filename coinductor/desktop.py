from __future__ import annotations

import os
from pathlib import Path
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from .controller import AppController
from .paths import bootstrap_data_dir, resolve_data_dir
from .tray import CoinductorTray


def main() -> int:
    data_dir = resolve_data_dir()
    if data_dir is not None:
        bootstrap_data_dir(data_dir)
        os.chdir(data_dir)

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
