# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project_root = Path(SPECPATH).parent

a = Analysis(
    [str(project_root / "packaging" / "run_coinductor.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / "coinductor" / "qml"), "coinductor/qml"),
        (str(project_root / "coinductor" / "assets" / "guides"), "coinductor/assets/guides"),
        (str(project_root / "coinductor" / "coinductor.ico"), "coinductor"),
        (str(project_root / "config.example.toml"), "."),
    ],
    # Imported inside functions, so PyInstaller's static analysis never sees
    # them. Without these the frozen app silently loses the system TLS trust
    # store and the OS credential store, and falls back to weaker behaviour
    # instead of failing loudly.
    hiddenimports=[
        "truststore",                 # binance_client._ssl_context
        "certifi",                    # its fallback
        "keyring",                    # secret_store._keyring
        "keyring.backends.Windows",   # the backend that actually stores keys
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Qt ships everything; the QML here imports only QtQuick, QtQuick.Controls
    # (+Material), QtQuick.Layouts and QtQuick.Dialogs. WebEngine alone is
    # 196 MB of a 423 MB bundle and nothing references it.
    # opengl32sw.dll is deliberately kept: it is the software rendering
    # fallback for machines without usable GPU drivers.
    excludes=[
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtWebChannel",
        "PySide6.QtWebSockets",
        "PySide6.QtQuick3D",
        "PySide6.Qt3DCore",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtDesigner",
        "PySide6.QtHelp",
        "PySide6.QtTest",
        "PySide6.QtBluetooth",
        "PySide6.QtNfc",
        "PySide6.QtSerialPort",
        "PySide6.QtSql",
        "tkinter",
    ],
    noarchive=False,
)

# PySide6's hook copies the whole Qt runtime regardless of `excludes`, which
# only prunes Python modules - so the DLLs and QML plugin trees have to be
# dropped from the collected tables by hand. WebEngine alone was 196 MB of a
# 423 MB bundle, and the QML here imports only QtQuick, QtQuick.Controls
# (+Material), QtQuick.Layouts and QtQuick.Dialogs.
#
# Verified by running the built exe, not just by building it: over-pruning
# breaks QML plugin loading at start-up, which no unit test would catch.
_UNUSED_QT = (
    "WebEngine", "WebChannel", "WebSockets", "WebView",
    "Quick3D", "Qt63D", "Charts", "DataVisualization",
    "Multimedia", "Qt6Pdf", "Designer", "QtHelp",
    "Bluetooth", "Nfc", "SerialPort", "Qt6Sql", "Qt6Test",
)


def _keep(entry) -> bool:
    name = entry[0].replace("\\", "/")
    return not any(token.lower() in name.lower() for token in _UNUSED_QT)


a.binaries = [entry for entry in a.binaries if _keep(entry)]
a.datas = [entry for entry in a.datas if _keep(entry)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Coinductor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(project_root / "coinductor" / "coinductor.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Coinductor",
)
