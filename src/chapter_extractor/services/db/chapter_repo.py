from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import Engine, select, text
from sqlalchemy.orm import Session

from chapter_extractor.domain.models import (
    Chapter,
    ChapterSummary,
    ChapterVersion,
    SearchHit,
)
from chapter_extractor.services.db.mappers import (
    ChapterMapper,
    ChapterVersionMapper,
    DateTimeCodec,
)
from chapter_extractor.services.db.tables_project import (
    ChapterRow,
    ChapterVersionRow,
)


class SqlAlchemyChapterRepository:
    """All chapter operations against a single project DB.

    Method names match `IChapterRepository`. Internally uses SQLAlchemy 2.0
    `select()` / Session. App code never sees raw SQL except for FTS5 search
    which is unavoidable (FTS5 is a virtual-table-only feature).
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ─── CRUD ────────────────────────────────────────────────────

    def add(self, chapter: Chapter) -> Chapter:
        return self.add_many([chapter])[0]

    def add_many(self, chapters: list[Chapter]) -> list[Chapter]:
        if not chapters:
            return []
        added: list[Chapter] = []
        with Session(self._engine) as session, session.begin():
            for ch in chapters:
                row = ChapterRow(
                    number=ch.number,
                    title=ch.title,
                    content=ch.content,
                    word_count=ch.word_count,
                    status=ch.status.name,
                    created_at=DateTimeCodec.encode(ch.created_at) or datetime.now().isoformat(),
                    modified_at=DateTimeCodec.encode(ch.modified_at) or datetime.now().isoformat(),
                    deleted_at=DateTimeCodec.encode(ch.deleted_at),
                )
                session.add(row)
                session.flush()
                ch.id = row.id
                added.append(ch)
        return added

    def get_by_number(self, number: int) -> Chapter | None:
        with Session(self._engine) as session:
            row = session.scalars(
                select(ChapterRow).where(
                    ChapterRow.number == number,
                    ChapterRow.deleted_at.is_(None),
                )
            ).first()
            return ChapterMapper.to_domain(row) if row else None

    def get_by_id(self, chapter_id: int) -> Chapter | None:
        with Session(self._engine) as session:
            row = session.get(ChapterRow, chapter_id)
            return ChapterMapper.to_domain(row) if row else None

    def update_content(self, chapter_id: int, title: str, content: str) -> Chapter:
        with Session(self._engine) as session, session.begin():
            row = session.get(ChapterRow, chapter_id)
            if row is None:
                raise KeyError(f"Chapter id {chapter_id} not found")
            row.title = title
            row.content = content
            row.word_count = len(content.split())
            row.modified_at = datetime.now().isoformat()
            row.status = "MODIFIED"
            session.flush()
            return ChapterMapper.to_domain(row)

    def list_summaries(self) -> list[ChapterSummary]:
        with Session(self._engine) as session:
            rows = session.scalars(
                select(ChapterRow)
                .where(ChapterRow.deleted_at.is_(None))
                .order_by(ChapterRow.number.asc())
            ).all()
            return [ChapterMapper.summary_from_row(r) for r in rows]

    def list_trash(self) -> list[ChapterSummary]:
        with Session(self._engine) as session:
            rows = session.scalars(
                select(ChapterRow)
                .where(ChapterRow.deleted_at.is_not(None))
                .order_by(ChapterRow.deleted_at.desc())
            ).all()
            return [ChapterMapper.summary_from_row(r) for r in rows]

    # ─── Soft delete + restore + retention ───────────────────────

    def soft_delete(self, chapter_id: int) -> None:
        with Session(self._engine) as session, session.begin():
            row = session.get(ChapterRow, chapter_id)
            if row is None:
                raise KeyError(f"Chapter id {chapter_id} not found")
            row.deleted_at = datetime.now().isoformat()

    def restore(self, chapter_id: int) -> Chapter:
        with Session(self._engine) as session, session.begin():
            row = session.get(ChapterRow, chapter_id)
            if row is None:
                raise KeyError(f"Chapter id {chapter_id} not found")
            row.deleted_at = None
            row.modified_at = datetime.now().isoformat()
            session.flush()
            return ChapterMapper.to_domain(row)

    def purge_expired(self, retention_days: int) -> int:
        """Hard-delete soft-deleted chapters older than retention_days. Returns count."""
        if retention_days < 0:
            raise ValueError("retention_days must be >= 0")
        cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat()
        with Session(self._engine) as session, session.begin():
            rows = session.scalars(
                select(ChapterRow)
                .where(ChapterRow.deleted_at.is_not(None))
                .where(ChapterRow.deleted_at < cutoff)
            ).all()
            count = len(rows)
            for r in rows:
                session.delete(r)
            return count

    # ─── Versioning ──────────────────────────────────────────────

    def list_versions(self, chapter_id: int) -> list[ChapterVersion]:
        with Session(self._engine) as session:
            rows = session.scalars(
                select(ChapterVersionRow)
                .where(ChapterVersionRow.chapter_id == chapter_id)
                .order_by(ChapterVersionRow.valid_from.desc())
            ).all()
            return [ChapterVersionMapper.to_domain(r) for r in rows]

    def restore_version(self, version_id: int) -> Chapter:
        """Set chapter content to the given historical version. Triggers
        record this as a new edit row (edit_reason='edit'); we then bump the
        most-recent version's edit_reason to 'restore' so the trail is clear."""
        with Session(self._engine) as session, session.begin():
            version = session.get(ChapterVersionRow, version_id)
            if version is None:
                raise KeyError(f"Version id {version_id} not found")
            chapter = session.get(ChapterRow, version.chapter_id)
            if chapter is None:
                raise KeyError(f"Chapter id {version.chapter_id} no longer exists")
            chapter.title = version.title
            chapter.content = version.content
            chapter.word_count = version.word_count
            chapter.modified_at = datetime.now().isoformat()
            chapter.status = "MODIFIED"
            session.flush()
            # Update the just-inserted version row's edit_reason to 'restore'
            session.execute(
                text(
                    "UPDATE chapter_versions SET edit_reason = 'restore' "
                    "WHERE chapter_id = :cid AND valid_to IS NULL"
                ),
                {"cid": chapter.id},
            )
            session.flush()
            return ChapterMapper.to_domain(chapter)

    # ─── Search (FTS5) ───────────────────────────────────────────

    def search(self, query: str, limit: int = 50) -> list[SearchHit]:
        """FTS5 MATCH search. Title weighted 2x via BM25. Returns ranked hits."""
        if not query.strip():
            return []
        sql = text(
            """
            SELECT c.id, c.number, c.title,
                   snippet(chapters_fts, 1, '«', '»', '…', 24) AS preview,
                   bm25(chapters_fts, 2.0, 1.0) AS rank
              FROM chapters_fts
              JOIN chapters c ON c.id = chapters_fts.rowid
             WHERE chapters_fts MATCH :q
               AND c.deleted_at IS NULL
             ORDER BY rank
             LIMIT :lim
            """
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"q": query, "lim": limit}).fetchall()
        return [
            SearchHit(
                chapter_id=int(r[0]),
                number=int(r[1]),
                title=str(r[2]),
                snippet=str(r[3]),
                rank=float(r[4]),
            )
            for r in rows
        ]
