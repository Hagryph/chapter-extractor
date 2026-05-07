from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from chapter_extractor.domain.models import Chapter, ParseResult
from chapter_extractor.domain.protocols import IChapterRepository, IParser


class BatchInputViewModel(QObject):
    """Drives the batch-input dialog. Live-parses raw text on demand and
    commits the parsed chapters via the repository."""

    preview_changed = Signal(object)   # ParseResult
    commit_succeeded = Signal(int)      # count added
    commit_failed = Signal(str)         # error message

    def __init__(self, parser: IParser, repo: IChapterRepository) -> None:
        super().__init__()
        self._parser = parser
        self._repo = repo
        self._last_result: ParseResult | None = None

    @property
    def last_result(self) -> ParseResult | None:
        return self._last_result

    def preview(self, raw_text: str) -> ParseResult:
        result = self._parser.parse(raw_text)
        self._last_result = result
        self.preview_changed.emit(result)
        return result

    def commit(self, raw_text: str) -> list[Chapter]:
        result = self.preview(raw_text)
        if result.is_empty:
            self.commit_failed.emit("No chapter headers detected.")
            return []
        try:
            added = self._repo.add_many(result.chapters)
        except Exception as exc:  # noqa: BLE001
            self.commit_failed.emit(str(exc))
            return []
        self.commit_succeeded.emit(len(added))
        return added
