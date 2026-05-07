from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from chapter_extractor.services.db.orm_base import ProjectBase


class ProjectMetaRow(ProjectBase):
    __tablename__ = "project_meta"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_project_meta_singleton"),
        CheckConstraint(
            "theme_mode IN ('light','dark','auto')", name="ck_project_meta_theme"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False, default=1)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    font_size: Mapped[int] = mapped_column(Integer, nullable=False, default=16)
    line_spacing: Mapped[float] = mapped_column(nullable=False, default=1.6)
    column_width: Mapped[int] = mapped_column(Integer, nullable=False, default=66)
    theme_mode: Mapped[str] = mapped_column(String, nullable=False, default="auto")
    soft_delete_retention_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=7
    )


class ChapterRow(ProjectBase):
    __tablename__ = "chapters"
    __table_args__ = (
        CheckConstraint(
            "status IN ('NEW','EXTRACTED','MODIFIED','MISSING_FILE')",
            name="ck_chapters_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="EXTRACTED")
    created_at: Mapped[str] = mapped_column(String, nullable=False, default_factory=lambda: datetime.now().isoformat())
    modified_at: Mapped[str] = mapped_column(String, nullable=False, default_factory=lambda: datetime.now().isoformat())
    deleted_at: Mapped[str | None] = mapped_column(String, nullable=True, default=None)


class ChapterVersionRow(ProjectBase):
    __tablename__ = "chapter_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_from: Mapped[str] = mapped_column(String, nullable=False)
    valid_to: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    edit_reason: Mapped[str] = mapped_column(String, nullable=False, default="auto")


# Non-declarative indexes
Index("idx_versions_chapter", ChapterVersionRow.chapter_id, ChapterVersionRow.valid_from.desc())


# Raw DDL for things SQLAlchemy can't fully model: partial indexes, virtual tables,
# triggers. Applied right after Base.metadata.create_all() during migration.
PROJECT_RAW_DDL = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_chapters_number_active
    ON chapters(number) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_chapters_deleted_at
    ON chapters(deleted_at) WHERE deleted_at IS NOT NULL;

CREATE VIRTUAL TABLE IF NOT EXISTS chapters_fts USING fts5(
    title, content,
    content        = 'chapters',
    content_rowid  = 'id',
    tokenize       = 'unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS chapters_ai AFTER INSERT ON chapters
WHEN new.deleted_at IS NULL
BEGIN
    INSERT INTO chapters_fts(rowid, title, content)
    VALUES (new.id, new.title, new.content);
END;

CREATE TRIGGER IF NOT EXISTS chapters_ad AFTER DELETE ON chapters
BEGIN
    INSERT INTO chapters_fts(chapters_fts, rowid, title, content)
    VALUES ('delete', old.id, old.title, old.content);
END;

CREATE TRIGGER IF NOT EXISTS chapters_au AFTER UPDATE ON chapters
BEGIN
    INSERT INTO chapters_fts(chapters_fts, rowid, title, content)
    VALUES ('delete', old.id, old.title, old.content);
    INSERT INTO chapters_fts(rowid, title, content)
    VALUES (new.id, new.title, new.content);
END;

-- Versioning triggers (SCD Type 2 history capture)
CREATE TRIGGER IF NOT EXISTS chapters_version_on_insert
AFTER INSERT ON chapters
WHEN new.deleted_at IS NULL
BEGIN
    INSERT INTO chapter_versions
        (chapter_id, title, content, word_count, valid_from, valid_to, edit_reason)
    VALUES
        (new.id, new.title, new.content, new.word_count,
         strftime('%Y-%m-%dT%H:%M:%f', 'now'), NULL, 'extract');
END;

CREATE TRIGGER IF NOT EXISTS chapters_version_on_update
AFTER UPDATE OF title, content ON chapters
WHEN old.deleted_at IS NULL AND new.deleted_at IS NULL
  AND (old.title <> new.title OR old.content <> new.content)
BEGIN
    UPDATE chapter_versions
       SET valid_to = strftime('%Y-%m-%dT%H:%M:%f', 'now')
     WHERE chapter_id = old.id AND valid_to IS NULL;

    INSERT INTO chapter_versions
        (chapter_id, title, content, word_count, valid_from, valid_to, edit_reason)
    VALUES
        (new.id, new.title, new.content, new.word_count,
         strftime('%Y-%m-%dT%H:%M:%f', 'now'), NULL, 'edit');
END;

-- Cap chapter_versions at 20 per chapter (configurable later via app).
CREATE TRIGGER IF NOT EXISTS chapter_versions_cap
AFTER INSERT ON chapter_versions
BEGIN
    DELETE FROM chapter_versions
     WHERE chapter_id = new.chapter_id
       AND id NOT IN (
           SELECT id FROM chapter_versions
            WHERE chapter_id = new.chapter_id
            ORDER BY valid_from DESC
            LIMIT 20
       );
END;

-- Views
CREATE VIEW IF NOT EXISTS v_chapter_summary AS
SELECT id, number, title, word_count, status, created_at, modified_at
  FROM chapters
 WHERE deleted_at IS NULL
 ORDER BY number ASC;

CREATE VIEW IF NOT EXISTS v_chapter_trash AS
SELECT id, number, title, word_count, status, created_at, modified_at, deleted_at
  FROM chapters
 WHERE deleted_at IS NOT NULL
 ORDER BY deleted_at DESC;
"""


__all__ = [
    "ProjectMetaRow",
    "ChapterRow",
    "ChapterVersionRow",
    "PROJECT_RAW_DDL",
    "text",  # re-export for convenience
]
