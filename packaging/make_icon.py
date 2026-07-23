"""Generate coinductor/coinductor.ico (and .png) from the in-app logo.

Renders packaging/logo_icon.qml offscreen on a transparent background and
packs a multi-resolution Windows .ico. Run when the logo changes:

    python packaging/make_icon.py
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QML = PROJECT_ROOT / "packaging" / "logo_icon.qml"
PNG_OUT = PROJECT_ROOT / "coinductor" / "coinductor.png"
ICO_OUT = PROJECT_ROOT / "coinductor" / "coinductor.ico"
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication([])
    view = QQuickView()
    view.setColor(Qt.transparent)
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(256, 256)
    view.setSource(QUrl.fromLocalFile(str(QML)))
    if view.status() != QQuickView.Ready:
        print("QML failed to load:", [e.toString() for e in view.errors()])
        return 1
    app.processEvents()
    app.processEvents()
    image = view.grabWindow()
    image.save(str(PNG_OUT))

    from PIL import Image

    base = Image.open(PNG_OUT).convert("RGBA")
    base.save(ICO_OUT, format="ICO", sizes=[(s, s) for s in ICO_SIZES])
    print(f"wrote {PNG_OUT} and {ICO_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
