from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from chapter_extractor.domain.models import ParseResult
from chapter_extractor.viewmodels.batch_input_vm import BatchInputViewModel
from chapter_extractor.views.style import ViewStyle


class BatchInputDialog(QDialog):
    """Modal dialog: paste → live preview → commit.

    Per Qt 6 QPlainTextEdit docs ("significantly more efficient for large
    document operations"), the paste area is QPlainTextEdit, not QTextEdit.

    Live-preview pattern uses a QTimer single-shot debounce (300ms) to avoid
    re-parsing on every keystroke when the user pastes a multi-MB block.
    """

    DEBOUNCE_MS = 300

    def __init__(self, vm: BatchInputViewModel, parent=None) -> None:
        super().__init__(parent)
        self._vm = vm
        self.setWindowTitle("Add Chapters")
        self.setModal(True)
        self.resize(900, 620)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(self.DEBOUNCE_MS)
        self._debounce.timeout.connect(self._do_preview)

        self._build_ui()
        self._wire_signals()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
        )
        outer.setSpacing(ViewStyle.GRID)

        instructions = QLabel(
            "Paste a batch of chapters below. Headers in the form "
            "<b>Chapter N: Title</b> will be detected automatically."
        )
        instructions.setWordWrap(True)
        outer.addWidget(instructions)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: paste area
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(ViewStyle.GRID)
        left_layout.addWidget(QLabel("Batch input"))
        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText(
            "Chapter 51: Ais Wallenstein\n…body…\n\n. . .\n\nChapter 52: …"
        )
        # Monospace font helps users line up structure.
        font = self._editor.font()
        font.setFamily("Consolas, Menlo, monospace")
        self._editor.setFont(font)
        left_layout.addWidget(self._editor, stretch=1)
        splitter.addWidget(left)

        # Right: detected chapters preview
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(ViewStyle.GRID)
        self._summary_label = QLabel("No chapters detected.")
        right_layout.addWidget(self._summary_label)
        self._preview_list = QListWidget()
        right_layout.addWidget(self._preview_list, stretch=1)
        self._warnings_label = QLabel("")
        self._warnings_label.setWordWrap(True)
        self._warnings_label.setStyleSheet("color: #d97706;")  # amber for warnings
        right_layout.addWidget(self._warnings_label)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        outer.addWidget(splitter, stretch=1)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Add Chapters")
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        outer.addWidget(self._buttons)

    def _wire_signals(self) -> None:
        self._editor.textChanged.connect(self._schedule_preview)
        self._vm.preview_changed.connect(self._render_preview)
        self._vm.commit_succeeded.connect(self._on_commit_succeeded)
        self._vm.commit_failed.connect(self._on_commit_failed)

    # ─── Slots ──────────────────────────────────────────────────

    def _schedule_preview(self) -> None:
        self._debounce.start()

    def _do_preview(self) -> None:
        self._vm.preview(self._editor.toPlainText())

    def _render_preview(self, result: ParseResult) -> None:
        self._preview_list.clear()
        for ch in result.chapters:
            self._preview_list.addItem(
                f"Chapter {ch.number}: {ch.title}  ({ch.word_count} words)"
            )
        n = len(result.chapters)
        if n == 0:
            self._summary_label.setText("No chapters detected.")
        else:
            self._summary_label.setText(
                f"<b>{n}</b> chapter{'s' if n != 1 else ''} detected."
            )
        if result.warnings:
            self._warnings_label.setText(
                "⚠ " + "<br>⚠ ".join(w.message for w in result.warnings)
            )
        else:
            self._warnings_label.clear()
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(n > 0)

    def _on_accept(self) -> None:
        self._vm.commit(self._editor.toPlainText())

    def _on_commit_succeeded(self, count: int) -> None:
        del count
        self.accept()

    def _on_commit_failed(self, message: str) -> None:
        self._warnings_label.setText(f"⚠ {message}")
