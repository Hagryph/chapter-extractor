from __future__ import annotations

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt

from chapter_extractor.domain.models import ChapterSummary
from chapter_extractor.viewmodels.chapter_list_model import ChapterListRoles


class ChapterFilterProxy(QSortFilterProxyModel):
    """Case-insensitive substring filter over chapter title and number.

    Live-filters as the user types in the search box. Empty filter shows all.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._needle = ""

    def set_needle(self, text: str) -> None:
        self._needle = (text or "").strip().lower()
        # invalidateRowsFilter() (Qt 5.15+) replaces deprecated invalidateFilter()
        self.invalidateRowsFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._needle:
            return True
        model = self.sourceModel()
        if model is None:
            return True
        idx = model.index(source_row, 0, source_parent)
        summary: ChapterSummary | None = model.data(idx, ChapterListRoles.SUMMARY)
        if summary is None:
            return True
        if self._needle in summary.title.lower():
            return True
        return self._needle in str(summary.number)
