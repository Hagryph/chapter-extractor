from __future__ import annotations

from datetime import datetime
from pathlib import Path

from chapter_extractor.domain.enums import ChapterStatus, EditReason, ThemeMode
from chapter_extractor.domain.models import (
    Chapter,
    ChapterSummary,
    ChapterVersion,
    Project,
    ProjectSettings,
    ProjectSummary,
)
from chapter_extractor.services.db.tables_project import (
    ChapterRow,
    ChapterVersionRow,
    ProjectMetaRow,
)
from chapter_extractor.services.db.tables_registry import ProjectRow


class DateTimeCodec:
    """ISO-8601 string ⇄ datetime, with naive-datetime support.
    Stored as TEXT in SQLite for portability."""

    @staticmethod
    def encode(dt: datetime | None) -> str | None:
        return dt.isoformat() if dt is not None else None

    @staticmethod
    def decode(s: str | None) -> datetime | None:
        if s is None:
            return None
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None


class ChapterMapper:
    @staticmethod
    def to_domain(row: ChapterRow) -> Chapter:
        return Chapter(
            number=row.number,
            title=row.title,
            content=row.content,
            filename="",
            file_path=Path(""),
            status=ChapterStatus[row.status],
            word_count=row.word_count,
            created_at=DateTimeCodec.decode(row.created_at) or datetime.now(),
            modified_at=DateTimeCodec.decode(row.modified_at) or datetime.now(),
            deleted_at=DateTimeCodec.decode(row.deleted_at),
            id=row.id,
        )

    @staticmethod
    def summary_from_row(row: ChapterRow) -> ChapterSummary:
        return ChapterSummary(
            id=row.id,
            number=row.number,
            title=row.title,
            word_count=row.word_count,
            status=ChapterStatus[row.status],
            modified_at=DateTimeCodec.decode(row.modified_at) or datetime.now(),
            deleted_at=DateTimeCodec.decode(row.deleted_at),
        )


class ChapterVersionMapper:
    @staticmethod
    def to_domain(row: ChapterVersionRow) -> ChapterVersion:
        try:
            reason = EditReason(row.edit_reason)
        except ValueError:
            reason = EditReason.AUTO
        return ChapterVersion(
            id=row.id,
            chapter_id=row.chapter_id,
            title=row.title,
            content=row.content,
            word_count=row.word_count,
            valid_from=DateTimeCodec.decode(row.valid_from) or datetime.now(),
            valid_to=DateTimeCodec.decode(row.valid_to),
            edit_reason=reason,
        )


class ProjectMapper:
    @staticmethod
    def to_domain(row: ProjectMetaRow, root_path: Path) -> Project:
        try:
            theme = ThemeMode(row.theme_mode)
        except ValueError:
            theme = ThemeMode.AUTO
        settings = ProjectSettings(
            font_size=row.font_size,
            line_spacing=row.line_spacing,
            column_width=row.column_width,
            theme_mode=theme,
            soft_delete_retention_days=row.soft_delete_retention_days,
        )
        return Project(
            name=row.name,
            root_path=root_path,
            created_at=DateTimeCodec.decode(row.created_at) or datetime.now(),
            settings=settings,
        )


class ProjectSummaryMapper:
    @staticmethod
    def to_domain(row: ProjectRow) -> ProjectSummary:
        return ProjectSummary(
            id=row.id,
            name=row.name,
            root_path=Path(row.root_path),
            created_at=DateTimeCodec.decode(row.created_at) or datetime.now(),
            last_opened_at=DateTimeCodec.decode(row.last_opened_at),
            pinned=bool(row.pinned),
        )
