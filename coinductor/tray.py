"""The tray icon: the app's only presence once the window is closed.

Kept out of the controller because it has to outlive the window. The whole
point of a scheduled run is that it finishes while nobody is looking at one,
and a notification posted from a widget that no longer exists posts nowhere.

Opt-in. An app holding exchange credentials that keeps running after you close
it, without saying so, is the kind of surprise that loses trust - so closing
the window exits unless the user has turned this on, and the icon is visible
the whole time it is active.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .service_strings import service_text


class CoinductorTray:
    """Wraps QSystemTrayIcon, or stands in for it where there is no tray."""

    def __init__(self, controller, icon_path: Path | None = None) -> None:
        self.controller = controller
        self._icon = None
        self._menu = None
        if not self.available():
            return

        icon = QIcon(str(icon_path)) if icon_path and icon_path.exists() else QIcon()
        self._icon = QSystemTrayIcon(icon)
        self._icon.setToolTip("Coinductor")
        self._build_menu()
        self._icon.activated.connect(self._on_activated)
        controller.trayMessageRequested.connect(self.notify)

    @staticmethod
    def available() -> bool:
        """False on a desktop with no notification area, and in tests."""
        try:
            return QSystemTrayIcon.isSystemTrayAvailable()
        except Exception:
            return False

    def _build_menu(self) -> None:
        language = getattr(self.controller, "_wizard_language", "en")
        self._menu = QMenu()
        self._menu.addAction(service_text("tray_open", language), self.show_window)
        self._menu.addAction(
            service_text("tray_run_now", language), self.controller.runAutomaticAnalysis
        )
        self._menu.addSeparator()
        # Quit is explicit and always present. A tray app that can only be
        # stopped through Task Manager is a tray app people uninstall.
        self._menu.addAction(service_text("tray_quit", language), self.quit)
        self._icon.setContextMenu(self._menu)

    def retranslate(self) -> None:
        """Rebuild the menu after a language change."""
        if self._icon is not None:
            self._build_menu()

    def show(self) -> None:
        if self._icon is not None:
            self._icon.show()

    def hide(self) -> None:
        if self._icon is not None:
            self._icon.hide()

    def notify(self, title: str, body: str) -> None:
        if self._icon is not None and self._icon.isVisible():
            self._icon.showMessage(title, body, QSystemTrayIcon.Information, 12_000)

    def show_window(self) -> None:
        window = self._root_window()
        if window is None:
            return
        window.setProperty("visible", True)
        # A hidden window can come back minimised behind everything; these two
        # are what actually bring it in front of the user.
        window.setProperty("visibility", 2)  # Windowed
        if hasattr(window, "requestActivate"):
            window.requestActivate()

    def quit(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _on_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_window()

    def _root_window(self):
        # desktop.py passes the QML engine as the controller's Qt parent, so
        # that is where the window lives. None in tests, and on the way down.
        engine = self.controller.parent() if hasattr(self.controller, "parent") else None
        objects = engine.rootObjects() if hasattr(engine, "rootObjects") else []
        return objects[0] if objects else None
