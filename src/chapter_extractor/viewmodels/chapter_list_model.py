from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from chapter_extractor.domain.enums import ChapterStatus
from chapter_extractor.domain.models import ChapterSummary


class ChapterListRoles:
    """Custom Qt item-data roles. Use ints offset from UserRole."""

    SUMMARY = Qt.ItemDataRole.UserRole + 1
    CHAPTER_ID = Qt.ItemDataRole.UserRole + 2
    NUMBER = Qt.ItemDataRole.UserRole + 3
    STATUS = Qt.ItemDataRole.UserRole + 4
    WORD_COUNT = Qt.ItemDataRole.UserRole + 5


class ChapterListModel(QAbstractListModel):
    """Qt list model wrapping a list of ChapterSummary.

    DisplayRole returns "Chapter NN: Title" for default rendering.
    Custom roles (SUMMARY/CHAPTER_ID/...) expose typed access for views.
    """

    _STATUS_PREFIX = {
        ChapterStatus.NEW: "•",
        ChapterStatus.EXTRACTED: "✓",
        ChapterStatus.MODIFIED: "✎",
        ChapterStatus.MISSING_FILE: "⚠",
    }

    def __init__(self, summaries: list[ChapterSummary] | None = None) -> None:
        super().__init__()
        self._summaries: list[ChapterSummary] = list(summaries or [])

    # ─── Required overrides ─────────────────────────────────────

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        if parent.isValid():
            return 0
        return len(self._summaries)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: ANN201
        if not index.isValid() or not (0 <= index.row() < len(self._summaries)):
            return None
        s = self._summaries[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            prefix = self._STATUS_PREFIX.get(s.status, "•")
            return f"{prefix}  {s.number:3d}  {s.title}"
        if role == Qt.ItemDataRole.ToolTipRole:
            return f"Chapter {s.number}: {s.title}\n{s.word_count} words"
        if role == ChapterListRoles.SUMMARY:
            return s
        if role == ChapterListRoles.CHAPTER_ID:
            return s.id
        if role == ChapterListRoles.NUMBER:
            return s.number
        if role == ChapterListRoles.STATUS:
            return s.status
        if role == ChapterListRoles.WORD_COUNT:
            return s.word_count
        return None

    # ─── Mutation API ───────────────────────────────────────────

    def replace_all(self, summaries: list[ChapterSummary]) -> None:
        """Atomic replace — emits modelReset so views fully repaint."""
        self.beginResetModel()
        self._summaries = list(summaries)
        self.endResetModel()

    def append(self, summary: ChapterSummary) -> None:
        row = len(self._summaries)
        self.beginInsertRows(QModelIndex(), row, row)
        self._summaries.append(summary)
        self.endInsertRows()

    def remove_at(self, row: int) -> ChapterSummary:
        if not (0 <= row < len(self._summaries)):
            raise IndexError(f"row {row} out of range")
        self.beginRemoveRows(QModelIndex(), row, row)
        removed = self._summaries.pop(row)
        self.endRemoveRows()
        return removed

    def update_at(self, row: int, summary: ChapterSummary) -> None:
        if not (0 <= row < len(self._summaries)):
            raise IndexError(f"row {row} out of range")
        self._summaries[row] = summary
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx)

    def summary_at(self, row: int) -> ChapterSummary | None:
        if 0 <= row < len(self._summaries):
            return self._summaries[row]
        return None

    def find_row_by_id(self, chapter_id: int) -> int:
        for i, s in enumerate(self._summaries):
            if s.id == chapter_id:
                return i
        return -1
