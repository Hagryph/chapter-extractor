from __future__ import annotations

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt

from chapter_extractor.domain.models import ChapterSummary
from chapter_extractor.viewmodels.chapter_list_model import ChapterListRoles


class ChapterFilterProxy(QSortFilterProxyModel):
    """Filters a ``ChapterListModel`` by case-insensitive substring against
    title and chapter-number.

    Why custom and not ``setFilterFixedString``? Built-in filtering matches
    only one column-and-role pair (``filterRole`` / ``filterKeyColumn``).
    We want the user's needle to match either *title* or *number*, so we
    override ``filterAcceptsRow``.

    Re-filter trigger: per Qt 6.13 docs, ``invalidateFilter`` and
    ``invalidateRowsFilter`` are deprecated. The supported call for custom
    filters whose criterion changed is ``invalidate()``.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._needle = ""

    def set_needle(self, text: str) -> None:
        self._needle = (text or "").strip().lower()
        self.invalidate()  # re-evaluate filterAcceptsRow for every source row

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
