from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from chapter_extractor.domain.models import Chapter, ChapterSummary
from chapter_extractor.domain.protocols import IChapterRepository
from chapter_extractor.viewmodels.chapter_filter_proxy import ChapterFilterProxy
from chapter_extractor.viewmodels.chapter_list_model import ChapterListModel


class ChapterListViewModel(QObject):
    """Orchestrates the chapter list: source model + filter proxy + selection.

    Views consume `proxy_model` (filtered + sortable) and listen to
    `selection_changed` to drive the reader pane.
    """

    selection_changed = Signal(object)  # ChapterSummary | None
    chapters_loaded = Signal(int)        # count
    chapter_added = Signal(int)          # chapter_id
    chapter_soft_deleted = Signal(int)   # chapter_id

    def __init__(self, repo: IChapterRepository) -> None:
        super().__init__()
        self._repo = repo
        self._source = ChapterListModel()
        self._proxy = ChapterFilterProxy()
        self._proxy.setSourceModel(self._source)
        self._selected_id: int | None = None

    # ─── Properties ─────────────────────────────────────────────

    @property
    def source_model(self) -> ChapterListModel:
        return self._source

    @property
    def proxy_model(self) -> ChapterFilterProxy:
        return self._proxy

    @property
    def selected_chapter_id(self) -> int | None:
        return self._selected_id

    # ─── Commands ───────────────────────────────────────────────

    def refresh(self) -> None:
        summaries = self._repo.list_summaries()
        self._source.replace_all(summaries)
        if self._selected_id and self._source.find_row_by_id(self._selected_id) == -1:
            self._set_selection(None)
        self.chapters_loaded.emit(len(summaries))

    def select_by_proxy_row(self, proxy_row: int) -> None:
        if proxy_row < 0 or proxy_row >= self._proxy.rowCount():
            self._set_selection(None)
            return
        proxy_idx = self._proxy.index(proxy_row, 0)
        source_idx = self._proxy.mapToSource(proxy_idx)
        summary = self._source.summary_at(source_idx.row())
        self._set_selection(summary)

    def select_by_id(self, chapter_id: int | None) -> None:
        if chapter_id is None:
            self._set_selection(None)
            return
        row = self._source.find_row_by_id(chapter_id)
        if row == -1:
            self._set_selection(None)
            return
        self._set_selection(self._source.summary_at(row))

    def set_search(self, needle: str) -> None:
        self._proxy.set_needle(needle)

    def add_extracted_chapters(self, chapters: list[Chapter]) -> list[Chapter]:
        added = self._repo.add_many(chapters)
        self.refresh()
        for ch in added:
            if ch.id is not None:
                self.chapter_added.emit(ch.id)
        return added

    def soft_delete_selected(self) -> None:
        if self._selected_id is None:
            return
        deleted_id = self._selected_id
        self._repo.soft_delete(deleted_id)
        self.refresh()
        self.chapter_soft_deleted.emit(deleted_id)

    # ─── Internals ──────────────────────────────────────────────

    def _set_selection(self, summary: ChapterSummary | None) -> None:
        new_id = summary.id if summary else None
        if new_id == self._selected_id:
            return
        self._selected_id = new_id
        self.selection_changed.emit(summary)
