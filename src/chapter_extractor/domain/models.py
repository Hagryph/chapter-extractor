from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from chapter_extractor.domain.enums import ChapterStatus


@dataclass(frozen=True, slots=True)
class ChapterHeader:
    """Result of locating a single `Chapter N: Title` line in a batch."""

    number: int
    title: str
    raw_match: str
    span: tuple[int, int]


@dataclass(frozen=True, slots=True)
class ParseWarning:
    message: str
    chapter_number: int | None = None


@dataclass
class Chapter:
    """A single extracted chapter. Mutable: status & file_path change after writing."""

    number: int
    title: str
    content: str
    filename: str
    file_path: Path
    status: ChapterStatus = ChapterStatus.NEW
    word_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def recompute_word_count(self) -> None:
        self.word_count = len(self.content.split())


@dataclass
class ParseResult:
    chapters: list[Chapter]
    warnings: list[ParseWarning] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.chapters

    @property
    def chapter_numbers(self) -> list[int]:
        return [c.number for c in self.chapters]
