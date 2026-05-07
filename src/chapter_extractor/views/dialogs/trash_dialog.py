from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from chapter_extractor.domain.models import ChapterSummary
from chapter_extractor.viewmodels.trash_vm import TrashViewModel
from chapter_extractor.views.style import ViewStyle


class TrashDialog(QDialog):
    """Soft-deleted chapters with restore + close."""

    def __init__(self, vm: TrashViewModel, retention_days: int, parent=None) -> None:
        super().__init__(parent)
        self._vm = vm
        self._retention_days = retention_days
        self.setWindowTitle("Trash")
        self.setModal(True)
        self.resize(560, 480)

        self._build_ui()
        self._vm.trash_changed.connect(self._refresh)
        self._vm.refresh()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
        )
        outer.setSpacing(ViewStyle.GRID)

        retention_lbl = QLabel(
            f"Soft-deleted chapters are permanently purged after "
            f"<b>{self._retention_days} days</b>."
        )
        outer.addWidget(retention_lbl)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        outer.addWidget(self._list, stretch=1)

        actions = QHBoxLayout()
        self._restore_btn = QPushButton("Restore selected")
        self._restore_btn.setEnabled(False)
        self._restore_btn.clicked.connect(self._on_restore)
        actions.addWidget(self._restore_btn)
        actions.addStretch()
        outer.addLayout(actions)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self._list.currentItemChanged.connect(
            lambda cur, _prev: self._restore_btn.setEnabled(cur is not None)
        )

    def _refresh(self) -> None:
        self._list.clear()
        for s in self._vm.items:
            text = f"Chapter {s.number}: {s.title}  ({s.word_count} words)"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, s)
            self._list.addItem(item)

    def _on_restore(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        summary: ChapterSummary = item.data(Qt.ItemDataRole.UserRole)
        self._vm.restore(summary.id)
