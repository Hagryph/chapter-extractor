from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from chapter_extractor.domain.enums import ChapterStatus, EditReason, ThemeMode

# ─── Parser-related (PR 1) ────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ChapterHeader:
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
    """A chapter, persisted or not. `id` is None until persisted."""

    number: int
    title: str
    content: str
    filename: str
    file_path: Path
    status: ChapterStatus = ChapterStatus.NEW
    word_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    deleted_at: datetime | None = None
    id: int | None = None

    def recompute_word_count(self) -> None:
        self.word_count = len(self.content.split())

    @property
    def is_active(self) -> bool:
        return self.deleted_at is None


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


# ─── DB-related (PR 2) ────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ChapterSummary:
    """Lightweight projection — never carries the full content. List-view friendly."""

    id: int
    number: int
    title: str
    word_count: int
    status: ChapterStatus
    modified_at: datetime
    deleted_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ChapterVersion:
    id: int
    chapter_id: int
    title: str
    content: str
    word_count: int
    valid_from: datetime
    valid_to: datetime | None
    edit_reason: EditReason


@dataclass(frozen=True, slots=True)
class SearchHit:
    chapter_id: int
    number: int
    title: str
    snippet: str
    rank: float


@dataclass
class ProjectSettings:
    font_size: int = 16
    line_spacing: float = 1.6
    column_width: int = 66
    theme_mode: ThemeMode = ThemeMode.AUTO
    soft_delete_retention_days: int = 7


@dataclass
class Project:
    name: str
    root_path: Path
    created_at: datetime = field(default_factory=datetime.now)
    settings: ProjectSettings = field(default_factory=ProjectSettings)

    @property
    def db_path(self) -> Path:
        return self.root_path / ".chapter_extractor" / "project.db"

    @property
    def metadata_dir(self) -> Path:
        return self.root_path / ".chapter_extractor"


@dataclass
class AppSettings:
    """App-wide settings (singleton row in registry.db)."""

    theme_mode: ThemeMode = ThemeMode.AUTO
    last_project_id: int | None = None
    soft_delete_retention_days: int = 7


@dataclass(frozen=True, slots=True)
class ProjectSummary:
    """Item in the registry's recent-projects view."""

    id: int
    name: str
    root_path: Path
    created_at: datetime
    last_opened_at: datetime | None
    pinned: bool = False
