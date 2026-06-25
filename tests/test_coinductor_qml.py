from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from coinductor.controller import AppController


def test_main_qml_loads(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlApplicationEngine()
    controller = AppController()
    engine.rootContext().setContextProperty("appController", controller)
    qml_path = Path(__file__).parents[1] / "coinductor" / "qml" / "Main.qml"

    engine.load(QUrl.fromLocalFile(str(qml_path.resolve())))

    assert engine.rootObjects()
    app.processEvents()
