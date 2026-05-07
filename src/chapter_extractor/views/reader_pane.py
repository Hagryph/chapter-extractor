from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from chapter_extractor.domain.models import Chapter
from chapter_extractor.viewmodels.reader_vm import ReaderViewModel
from chapter_extractor.views.style import ViewStyle
from chapter_extractor.views.widgets.reader_text import ReaderTextView


class ReaderPane(QWidget):
    """Right pane: reader text + action buttons (copy / pop-out / delete)."""

    def __init__(self, vm: ReaderViewModel) -> None:
        super().__init__()
        self._vm = vm
        self._build_ui()
        self._wire_signals()
        self._update_actions(None)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)  # ReaderTextView pads internally
        outer.setSpacing(0)

        self._text = ReaderTextView(self._vm)
        outer.addWidget(self._text, stretch=1)

        actions = QWidget()
        a_layout = QHBoxLayout(actions)
        a_layout.setContentsMargins(
            ViewStyle.PANE_PADDING,
            ViewStyle.GRID,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
        )
        a_layout.setSpacing(ViewStyle.GRID)

        self._copy_btn = QPushButton("📋 Copy")
        self._copy_btn.setToolTip("Copy chapter content to clipboard (Ctrl+Shift+C)")
        self._copy_btn.clicked.connect(self._vm.copy_current_content)

        self._pop_btn = QPushButton("↗ Pop Out")
        self._pop_btn.setToolTip("Open in a separate window (Ctrl+Shift+O)")
        self._pop_btn.clicked.connect(self._vm.pop_out)

        self._focus_btn = QPushButton("⛶ Focus")
        self._focus_btn.setToolTip("Cycle view modes (F11)")
        self._focus_btn.clicked.connect(self._vm.cycle_view_mode)

        a_layout.addStretch()
        a_layout.addWidget(self._copy_btn)
        a_layout.addWidget(self._pop_btn)
        a_layout.addWidget(self._focus_btn)
        outer.addWidget(actions)

    def _wire_signals(self) -> None:
        self._vm.chapter_loaded.connect(self._update_actions)

    def _update_actions(self, chapter: Chapter | None) -> None:
        enabled = chapter is not None
        self._copy_btn.setEnabled(enabled)
        self._pop_btn.setEnabled(enabled)
        self._focus_btn.setEnabled(enabled)
