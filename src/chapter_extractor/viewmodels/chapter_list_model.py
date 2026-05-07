from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from chapter_extractor.domain.enums import ChapterStatus
from chapter_extractor.domain.models import ChapterSummary


class ChapterListRoles:
    """Custom item-data roles. Per Qt convention, custom roles start at
    ``UserRole`` and increment. Each role is exposed via ``data(index, role)``.
    """

    SUMMARY = Qt.ItemDataRole.UserRole + 1
    CHAPTER_ID = Qt.ItemDataRole.UserRole + 2
    NUMBER = Qt.ItemDataRole.UserRole + 3
    STATUS = Qt.ItemDataRole.UserRole + 4
    WORD_COUNT = Qt.ItemDataRole.UserRole + 5


class ChapterListModel(QAbstractListModel):
    """Qt list model wrapping ``list[ChapterSummary]``.

    Per Qt 6 docs (https://doc.qt.io/qt-6/qabstractlistmodel.html), subclasses
    MUST implement ``rowCount`` and ``data``. "Well-behaved models" also
    implement ``headerData``. For resizable structures, use proper
    ``begin/endInsertRows`` / ``begin/endRemoveRows`` bracketing — emitting
    ``layoutChanged`` directly is supported but coarser-grained and views
    re-render the whole list.
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
        # parent is meaningful for tree models; for a flat list we return 0
        # whenever a non-root parent is queried.
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

    # ─── Optional but recommended ─────────────────────────────────

    def headerData(  # noqa: ANN201
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        # QListView ignores headers but per Qt docs well-behaved models
        # provide one anyway.
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and section == 0
        ):
            return "Chapter"
        return None

    # ─── Mutation API (each pairs proper begin/end signals) ──────

    def replace_all(self, summaries: list[ChapterSummary]) -> None:
        """Atomic replace. ``beginResetModel/endResetModel`` is the
        canonical way for a wholesale change — views fully invalidate."""
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
        # Per Qt docs, ``dataChanged.emit(topLeft, bottomRight)`` is the
        # right signal for in-place value changes (vs structural changes).
        self.dataChanged.emit(idx, idx)

    # ─── Read helpers ───────────────────────────────────────────

    def summary_at(self, row: int) -> ChapterSummary | None:
        if 0 <= row < len(self._summaries):
            return self._summaries[row]
        return None

    def find_row_by_id(self, chapter_id: int) -> int:
        for i, s in enumerate(self._summaries):
            if s.id == chapter_id:
                return i
        return -1
