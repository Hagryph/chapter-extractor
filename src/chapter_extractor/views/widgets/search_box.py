from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QLineEdit


class SearchBox(QLineEdit):
    """Search input with built-in clear button + Esc-to-clear shortcut.

    Inherits ``textChanged`` signal from QLineEdit — connect that directly
    to the proxy filter in the parent view.
    """

    def __init__(self, placeholder: str = "Search chapters…") -> None:
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setAccessibleName(placeholder)
        self.setMinimumHeight(32)
        self._install_escape_shortcut()

    def _install_escape_shortcut(self) -> None:
        shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        shortcut.activated.connect(self.clear)
