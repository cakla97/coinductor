from __future__ import annotations

import os
from pathlib import Path
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .controller import AppController
from .paths import bootstrap_data_dir, resolve_data_dir


def main() -> int:
    data_dir = resolve_data_dir()
    if data_dir is not None:
        bootstrap_data_dir(data_dir)
        os.chdir(data_dir)

    app = QGuiApplication(sys.argv)
    app.setApplicationName("Coinductor")
    app.setOrganizationName("Coinductor")

    engine = QQmlApplicationEngine()
    controller = AppController(engine)
    engine.rootContext().setContextProperty("appController", controller)
    qml_path = Path(__file__).parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path.resolve())))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
