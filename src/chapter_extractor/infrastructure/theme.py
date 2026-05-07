from __future__ import annotations

import contextlib

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from chapter_extractor.domain.enums import ThemeMode
from chapter_extractor.infrastructure.settings import SettingsStore
from chapter_extractor.views.theme.palettes import PaletteFactory
from chapter_extractor.views.theme.stylesheet import StylesheetBuilder
from chapter_extractor.views.theme.tokens import ThemeTokens


class ThemeManager:
    """Resolves the current ThemeMode → ThemeTokens → QSS → applies it.

    On AUTO, follows ``QGuiApplication.styleHints().colorScheme()`` (Qt 6.5+).
    Re-applies live whenever:
      - The user toggles theme via SettingsStore
      - The OS broadcasts a colorScheme change (system theme switch)
    """

    def __init__(self, app: QApplication, settings: SettingsStore) -> None:
        self._app = app
        self._settings = settings
        self._current: ThemeTokens | None = None

        self._settings.theme_changed.connect(self._on_theme_changed)
        hints = app.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(self._on_os_scheme_changed)

    @property
    def current_tokens(self) -> ThemeTokens | None:
        return self._current

    def apply_current(self) -> None:
        self.apply(self._settings.theme_mode)

    def apply(self, mode: ThemeMode) -> None:
        tokens = self._resolve_tokens(mode)
        self._current = tokens
        qss = StylesheetBuilder(tokens).build()
        self._app.setStyleSheet(qss)
        # Hint Qt's high-level color scheme so native dialogs match.
        # Older Qt versions don't expose setColorScheme — silently ignore;
        # the stylesheet alone is sufficient.
        with contextlib.suppress(AttributeError, TypeError):
            self._app.styleHints().setColorScheme(
                Qt.ColorScheme.Dark if tokens.is_dark else Qt.ColorScheme.Light
            )

    # ─── Internals ──────────────────────────────────────────────

    def _resolve_tokens(self, mode: ThemeMode) -> ThemeTokens:
        if mode == ThemeMode.DARK:
            return PaletteFactory.dark()
        if mode == ThemeMode.LIGHT:
            return PaletteFactory.light()
        return self._auto_tokens()

    def _auto_tokens(self) -> ThemeTokens:
        try:
            scheme = QGuiApplication.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Dark:
                return PaletteFactory.dark()
            if scheme == Qt.ColorScheme.Light:
                return PaletteFactory.light()
        except (AttributeError, TypeError):
            pass
        # Fallback: inspect window palette lightness.
        palette = QGuiApplication.palette()
        is_dark = palette.color(palette.ColorRole.Window).lightness() < 128
        return PaletteFactory.dark() if is_dark else PaletteFactory.light()

    def _on_theme_changed(self, mode: ThemeMode) -> None:
        self.apply(mode)

    def _on_os_scheme_changed(self) -> None:
        if self._settings.theme_mode == ThemeMode.AUTO:
            self.apply(ThemeMode.AUTO)
