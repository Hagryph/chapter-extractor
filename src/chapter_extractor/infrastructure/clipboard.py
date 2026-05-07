from __future__ import annotations

from PySide6.QtGui import QGuiApplication


class QtClipboard:
    """Minimal IClipboard impl over QGuiApplication.clipboard()."""

    def copy(self, text: str) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)
