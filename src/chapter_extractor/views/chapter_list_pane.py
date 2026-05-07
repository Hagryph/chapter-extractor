from __future__ import annotations

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chapter_extractor.viewmodels.chapter_list_vm import ChapterListViewModel
from chapter_extractor.views.style import ViewStyle
from chapter_extractor.views.widgets.search_box import SearchBox


class ChapterListPane(QWidget):
    """Centre pane: search box + chapter list + footer.

    The QListView is bound to the proxy model from ChapterListViewModel.
    Selection changes propagate via the selection model's currentChanged
    signal to ``vm.select_by_proxy_row``. Per Qt docs we hold a ref to the
    selection model as an instance attribute to avoid GC of the proxy.
    """

    def __init__(self, vm: ChapterListViewModel) -> None:
        super().__init__()
        self._vm = vm
        self._build_ui()
        self._wire_signals()
        self._update_count()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
        )
        outer.setSpacing(ViewStyle.GRID)

        self._search = SearchBox()
        outer.addWidget(self._search)

        self._list = QListView()
        self._list.setModel(self._vm.proxy_model)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setUniformItemSizes(True)
        self._list.setAlternatingRowColors(True)
        outer.addWidget(self._list, stretch=1)

        # Strong ref to the selection model: per
        # https://www.pythonguis.com/tutorials/pyside6-modelview-architecture/
        # connecting directly to selectionModel() result risks GC of the proxy.
        self._selection_model = self._list.selectionModel()

        self._add_btn = QPushButton("+ Add Chapters")
        self._add_btn.clicked.connect(self._on_add_clicked)
        outer.addWidget(self._add_btn)

        self._count_label = QLabel("0 chapters")
        self._count_label.setStyleSheet("opacity: 0.6;")
        outer.addWidget(self._count_label)

    def _wire_signals(self) -> None:
        self._search.textChanged.connect(self._vm.set_search)
        self._selection_model.currentChanged.connect(self._on_current_changed)
        self._vm.chapters_loaded.connect(self._on_chapters_loaded)
        self._vm.proxy_model.rowsInserted.connect(self._update_count)
        self._vm.proxy_model.rowsRemoved.connect(self._update_count)
        self._vm.proxy_model.modelReset.connect(self._update_count)
        self._vm.proxy_model.layoutChanged.connect(self._update_count)

    # ─── Slots ──────────────────────────────────────────────────

    def _on_current_changed(
        self, current: QModelIndex, previous: QModelIndex
    ) -> None:
        del previous
        if not current.isValid():
            self._vm.select_by_proxy_row(-1)
            return
        self._vm.select_by_proxy_row(current.row())

    def _on_chapters_loaded(self, count: int) -> None:
        del count
        # On full refresh the selection model loses its current row; re-sync
        # by clearing the visual selection so the user picks fresh.
        self._selection_model.clearCurrentIndex()
        self._update_count()

    def _on_add_clicked(self) -> None:
        # Real dialog ships in PR 6 (BatchInputDialog). For now we surface
        # the placeholder via the parent's request handler.
        parent = self.parentWidget()
        if hasattr(parent, "request_batch_input"):
            parent.request_batch_input()

    def _update_count(self, *_: object) -> None:
        n = self._vm.proxy_model.rowCount()
        self._count_label.setText(f"{n} chapter{'s' if n != 1 else ''}")

    # ─── Properties for tests ───────────────────────────────────

    @property
    def list_view(self) -> QListView:
        return self._list

    @property
    def search_box(self) -> SearchBox:
        return self._search
