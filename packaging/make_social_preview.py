"""Render the 1280x640 GitHub social preview card.

GitHub has no API for setting this image, so it is generated here and uploaded
by hand in Settings > General > Social preview. Kept in the repo so the card can
be regenerated when the tagline changes, rather than being a one-off export
nobody can reproduce.

    python packaging/make_social_preview.py
"""

from __future__ import annotations

from pathlib import Path

# Deliberately not the offscreen platform: on Windows it reports zero font
# families, so every glyph rendered as a tofu box. The native plugin draws into
# a QImage without ever showing a window, which is all this needs.

from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import (  # noqa: E402
    QColor,
    QFont,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPen,
)

WIDTH, HEIGHT = 1280, 640
BACKGROUND = QColor("#0e1117")
PANEL = QColor("#161b26")
BORDER = QColor("#232a39")
ACCENT = QColor("#2ecc80")
TEXT = QColor("#f2f5fa")
MUTED = QColor("#93a0b5")
WARN = QColor("#e8b339")

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "social-preview.png"


def _font(size: int, *, bold: bool = False) -> QFont:
    from PySide6.QtGui import QFontDatabase

    available = set(QFontDatabase.families())
    family = next((name for name in ("Segoe UI", "Calibri", "Arial", "DejaVu Sans") if name in available), "")
    font = QFont(family) if family else QFont()
    font.setPixelSize(size)
    font.setBold(bold)
    return font


def main() -> None:
    QGuiApplication([])
    image = QImage(WIDTH, HEIGHT, QImage.Format_ARGB32)
    image.fill(BACKGROUND)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    # A quiet wash from the top left, so the card is not a flat rectangle.
    wash = QLinearGradient(0, 0, WIDTH, HEIGHT)
    wash.setColorAt(0.0, QColor(46, 204, 128, 26))
    wash.setColorAt(0.55, QColor(14, 17, 23, 0))
    painter.fillRect(0, 0, WIDTH, HEIGHT, wash)

    # Accent rule down the left edge: the app's own sidebar signature.
    painter.fillRect(0, 0, 8, HEIGHT, ACCENT)

    left = 88

    # Wordmark.
    painter.setPen(QPen(TEXT))
    painter.setFont(_font(76, bold=True))
    painter.drawText(QRectF(left, 96, WIDTH - left - 80, 90), Qt.AlignLeft | Qt.AlignVCenter, "Coinductor")

    painter.setPen(QPen(ACCENT))
    painter.setFont(_font(27, bold=True))
    painter.drawText(
        QRectF(left, 186, WIDTH - left - 80, 40),
        Qt.AlignLeft | Qt.AlignVCenter,
        "Binance Spot portfolio assistant that runs on your own machine",
    )

    painter.setPen(QPen(MUTED))
    painter.setFont(_font(23))
    painter.drawText(
        QRectF(left, 232, 1000, 76),
        Qt.AlignLeft | Qt.TextWordWrap,
        "A deterministic risk engine decides. The AI only ever proposes - and never\n"
        "reaches a submit path without passing through it.",
    )

    # Three claims, each in its own panel.
    claims = (
        ("Local first", "No account, no telemetry.\nKeys stay in the OS vault."),
        ("Never auto-trades", "Every real order needs a\ntyped confirmation."),
        ("Bring your own model", "Ollama, or any OpenAI-\ncompatible endpoint."),
    )
    panel_w, panel_h, gap = 352, 148, 24
    top = 366
    for index, (title, body) in enumerate(claims):
        x = left + index * (panel_w + gap)
        rect = QRectF(x, top, panel_w, panel_h)
        painter.setBrush(PANEL)
        painter.setPen(QPen(BORDER, 1))
        painter.drawRoundedRect(rect, 14, 14)

        painter.setPen(QPen(ACCENT))
        painter.setFont(_font(21, bold=True))
        painter.drawText(QRectF(x + 22, top + 20, panel_w - 40, 30), Qt.AlignLeft | Qt.AlignVCenter, title)

        painter.setPen(QPen(MUTED))
        painter.setFont(_font(17))
        painter.drawText(QRectF(x + 22, top + 56, panel_w - 40, 72), Qt.AlignLeft | Qt.TextWordWrap, body)

    # Footer: what it is, and the honest disclaimer.
    painter.setPen(QPen(MUTED))
    painter.setFont(_font(18))
    painter.drawText(
        QRectF(left, HEIGHT - 84, 700, 30),
        Qt.AlignLeft | Qt.AlignVCenter,
        "Windows desktop  ·  Python + PySide6  ·  MIT",
    )
    painter.setPen(QPen(WARN))
    painter.setFont(_font(18, bold=True))
    painter.drawText(
        QRectF(WIDTH - 460, HEIGHT - 84, 380, 30),
        Qt.AlignRight | Qt.AlignVCenter,
        "Not financial advice",
    )

    painter.end()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(OUTPUT), "PNG")
    print(f"wrote {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB, {WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
