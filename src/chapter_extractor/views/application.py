from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from chapter_extractor.infrastructure.app_context import AppContext
from chapter_extractor.infrastructure.theme import ThemeManager
from chapter_extractor.viewmodels.main_vm import MainViewModel
from chapter_extractor.views.main_window import MainWindow


class Application:
    """Composition root for the GUI app.

    Order of construction matters: AppContext (bootstrap registry DB +
    settings) → QApplication → ThemeManager.apply_current() → MainViewModel
    → MainWindow.
    """

    def __init__(self, argv: list[str]) -> None:
        self._argv = argv
        self._qapp: QApplication | None = None
        self._ctx: AppContext | None = None
        self._theme: ThemeManager | None = None
        self._vm: MainViewModel | None = None
        self._window: MainWindow | None = None

    def run(self) -> int:
        self._qapp = QApplication.instance() or QApplication(self._argv)
        self._ctx = AppContext.bootstrap()
        self._theme = ThemeManager(self._qapp, self._ctx.settings)
        self._theme.apply_current()
        self._vm = MainViewModel(self._ctx)
        self._window = MainWindow(self._ctx, self._vm)
        self._window.show()
        try:
            return self._qapp.exec()
        finally:
            if self._ctx is not None:
                self._ctx.shutdown()


def main() -> int:
    return Application(sys.argv).run()
