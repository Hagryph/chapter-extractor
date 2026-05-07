from __future__ import annotations

from PySide6.QtWidgets import QApplication

from chapter_extractor.domain.enums import ThemeMode
from chapter_extractor.infrastructure.settings import SettingsStore


class ThemeManager:
    """Applies a modern flat theme (pyqtdarktheme). Listens to SettingsStore
    so theme changes propagate live without an app restart.
    """

    _FALLBACK_QSS = """
    QWidget { font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; }
    QPushButton { padding: 6px 14px; border-radius: 6px; }
    QListView { border-radius: 6px; padding: 4px; }
    QTextBrowser, QPlainTextEdit { border: none; }
    """

    def __init__(self, app: QApplication, settings: SettingsStore) -> None:
        self._app = app
        self._settings = settings
        self._settings.theme_changed.connect(self.apply)

    def apply_current(self) -> None:
        self.apply(self._settings.theme_mode)

    def apply(self, mode: ThemeMode) -> None:
        try:
            import qdarktheme  # type: ignore[import-not-found]

            qdarktheme.setup_theme(mode.value)
        except Exception:
            self._app.setStyleSheet(self._FALLBACK_QSS)
