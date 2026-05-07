from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy
from qframelesswindow import StandardTitleBar


class AppTitleBar(StandardTitleBar):
    """Custom titlebar for the main window.

    Reuses ``qframelesswindow.StandardTitleBar`` for the platform-correct
    minimize/maximize/close buttons (with native double-click-to-maximize and
    Win11 snap-layout integration), and prepends our app icon + name on the
    left so the chrome reads as a unified app bar.
    """

    TITLEBAR_HEIGHT = 36

    def __init__(self, parent, icon_path: str | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(self.TITLEBAR_HEIGHT)
        self.setProperty("role", "titlebar")

        # Hide the duplicate window-icon label that StandardTitleBar adds, so
        # we can render our own with consistent sizing.
        self.iconLabel.hide()
        self.titleLabel.hide()

        self._brand = QLabel()
        self._brand.setObjectName("brandLabel")
        self._brand.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self._brand.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        if icon_path:
            self._icon = QLabel()
            pix = QPixmap(icon_path).scaled(
                18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self._icon.setPixmap(pix)
            self._icon.setFixedWidth(28)
            self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self._icon = None  # type: ignore[assignment]

        # Insert brand into the existing horizontal layout BEFORE the spacer
        # used by min/max/close on the right. StandardTitleBar's layout is
        # accessible via .hBoxLayout (older API) or .layout() (current).
        layout = self.layout()
        if isinstance(layout, QHBoxLayout):
            insert_at = 0
            if self._icon is not None:
                layout.insertWidget(insert_at, self._icon)
                insert_at += 1
            layout.insertWidget(insert_at, self._brand)
            layout.insertStretch(insert_at + 1, 1)

    def set_title(self, text: str) -> None:
        self._brand.setText(text)

    def setWindowTitle(self, text: str) -> None:  # noqa: N802 — Qt API style
        self.set_title(text)
