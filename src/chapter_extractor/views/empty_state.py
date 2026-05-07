from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EmptyStateWidget(QWidget):
    """Placeholder shown in centre + reader panes when no project is open."""

    def __init__(self, message: str = "Create or open a project to begin.") -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 96, 48, 96)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 15px; opacity: 0.55;")
        label.setWordWrap(True)

        layout.addWidget(label)
