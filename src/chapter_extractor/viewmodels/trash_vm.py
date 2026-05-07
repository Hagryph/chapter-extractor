from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from chapter_extractor.domain.models import ChapterSummary
from chapter_extractor.domain.protocols import IChapterRepository


class TrashViewModel(QObject):
    """Soft-deleted chapters + restore command."""

    trash_changed = Signal()
    chapter_restored = Signal(int)

    def __init__(self, repo: IChapterRepository, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._repo = repo
        self._items: list[ChapterSummary] = []

    @property
    def items(self) -> list[ChapterSummary]:
        return list(self._items)

    def refresh(self) -> None:
        self._items = self._repo.list_trash()
        self.trash_changed.emit()

    def restore(self, chapter_id: int) -> None:
        self._repo.restore(chapter_id)
        self.refresh()
        self.chapter_restored.emit(chapter_id)
