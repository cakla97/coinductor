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
    assert "appController.checkBinanceLiveTrading" in qml
    assert "Enable mainnet preview" in qml
    assert "Arm guarded actions" in qml
    assert "Enable guarded live submit" in qml
    assert "appController.copyText" in qml
    assert "appController.lockLiveSubmit" in qml
    assert "Safety & readiness" in qml
    assert "appController.hasCompletedRealAnalysis" in qml
    assert "appController.hasReadyLivePreview" in qml
    assert "Layout.row: 2" in qml
    assert "Layout.row: 3" in qml
    assert "Manage live trading API" in qml
    assert "liveApiManagerDialog.open()" in qml
    assert "Credentials & Safety" not in qml
    assert "Permissions verified this session" in qml
    assert "safetyPhraseRow.implicitHeight + 24" in qml
    assert 'safetyAllowsLiveSubmit ? "#ee6b6e"' not in qml
