from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import qInstallMessageHandler, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from coinductor.controller import AppController


def test_main_qml_loads(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    messages: list[str] = []

    def capture_message(_mode, _context, message: str) -> None:
        messages.append(message)

    previous_handler = qInstallMessageHandler(capture_message)
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlApplicationEngine()
    try:
        controller = AppController(engine)
        engine.rootContext().setContextProperty("appController", controller)
        qml_path = Path(__file__).parents[1] / "coinductor" / "qml" / "Main.qml"

        engine.load(QUrl.fromLocalFile(str(qml_path.resolve())))

        assert engine.rootObjects()
        engine.rootObjects()[0].deleteLater()
        app.processEvents()
    finally:
        qInstallMessageHandler(previous_handler)

    assert not any("appController" in message and "null" in message for message in messages)


def test_main_qml_contains_separate_guarded_trade_and_oco_confirmations() -> None:
    qml_path = Path(__file__).parents[1] / "coinductor" / "qml" / "Main.qml"
    qml = qml_path.read_text(encoding="utf-8")

    assert "CONFIRM_MAINNET_ORDER" in qml
    assert "appController.submitGuardedTrade" in qml
    assert "CONFIRM_MAINNET_OCO" in qml
    assert "appController.submitGuardedOco" in qml
