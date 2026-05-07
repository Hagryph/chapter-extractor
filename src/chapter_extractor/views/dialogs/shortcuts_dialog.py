from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from chapter_extractor.domain.shortcuts import (
    ShortcutCatalog,
    ShortcutCategory,
    ShortcutSpec,
)
from chapter_extractor.views.style import ViewStyle


class ShortcutsDialog(QDialog):
    """Searchable cheat-sheet of every keyboard shortcut.

    Pattern from Google Docs / Trello: ``Ctrl+/`` brings up a one-screen
    reference. Search box at top filters in real time.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setModal(True)
        self.resize(640, 540)
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
        )
        outer.setSpacing(ViewStyle.GRID)

        header = QLabel("Press <b>Esc</b> to close. Type to filter.")
        outer.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter shortcuts…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search)
        outer.addWidget(self._search)

        self._tree = QTreeWidget()
        self._tree.setColumnCount(2)
        self._tree.setHeaderLabels(["Action", "Shortcut"])
        self._tree.setRootIsDecorated(False)
        self._tree.setIndentation(0)
        self._tree.setUniformRowHeights(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header_view = self._tree.header()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        outer.addWidget(self._tree, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _populate(self) -> None:
        self._tree.clear()
        for category in ShortcutCatalog.categories_in_order():
            self._add_category(category)
        self._tree.expandAll()

    def _add_category(self, category: ShortcutCategory) -> None:
        header = QTreeWidgetItem([category.value])
        header_font = header.font(0)
        header_font.setBold(True)
        header_font.setPointSize(header_font.pointSize() + 1)
        header.setFont(0, header_font)
        header.setFirstColumnSpanned(True)
        header.setFlags(header.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self._tree.addTopLevelItem(header)

        for spec in ShortcutCatalog.by_category(category):
            self._add_shortcut_row(spec)

    def _add_shortcut_row(self, spec: ShortcutSpec) -> None:
        row = QTreeWidgetItem([spec.label, self._format_shortcut(spec.key_sequence)])
        row.setToolTip(0, spec.status_tip)
        # Use a monospace-ish font for the shortcut column for alignment.
        f = QFont()
        f.setStyleHint(QFont.StyleHint.Monospace)
        row.setFont(1, f)
        self._tree.addTopLevelItem(row)

    @staticmethod
    def _format_shortcut(seq: str) -> str:
        # QKeySequence.toString gives the OS-localised version (e.g. "⌘+C" on macOS,
        # "Ctrl+C" on Windows). Per NN/g UI-copy guidance, equivalent shortcuts should
        # be available cross-OS — Qt handles this for us.
        return QKeySequence(seq).toString(QKeySequence.SequenceFormat.NativeText)

    def _on_search(self, needle: str) -> None:
        n = needle.strip().lower()
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            # Category headers always visible while searching (acts as group label).
            if item.isFirstColumnSpanned():
                item.setHidden(False)
                continue
            label = item.text(0).lower()
            shortcut = item.text(1).lower()
            visible = not n or n in label or n in shortcut
            item.setHidden(not visible)

        # If a category has no visible children, hide it.
        if n:
            self._hide_empty_categories()
        else:
            for i in range(self._tree.topLevelItemCount()):
                self._tree.topLevelItem(i).setHidden(False)

    def _hide_empty_categories(self) -> None:
        last_header_idx = -1
        last_header_has_visible = False
        last_header_item: QTreeWidgetItem | None = None
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item.isFirstColumnSpanned():
                if last_header_item is not None and not last_header_has_visible:
                    last_header_item.setHidden(True)
                last_header_idx = i
                last_header_item = item
                last_header_has_visible = False
            elif not item.isHidden():
                last_header_has_visible = True
        if last_header_item is not None and not last_header_has_visible:
            last_header_item.setHidden(True)
        del last_header_idx
