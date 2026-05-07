from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import Engine, text

from chapter_extractor.domain.enums import ChapterStatus, EditReason
from chapter_extractor.domain.models import Chapter
from chapter_extractor.services.db.chapter_repo import SqlAlchemyChapterRepository


def _make(number: int, title: str = "T", body: str = "lorem ipsum dolor sit amet") -> Chapter:
    ch = Chapter(
        number=number,
        title=title,
        content=body,
        filename=f"Chapter_{number:03d}.txt",
        file_path=Path(f"Chapter_{number:03d}.txt"),
        status=ChapterStatus.EXTRACTED,
    )
    ch.recompute_word_count()
    return ch


class TestCRUD:
    def test_add_assigns_id(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        out = repo.add(_make(1, "First"))
        assert out.id is not None and out.id > 0

    def test_get_by_number_roundtrip(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        repo.add(_make(51, "Ais Wallenstein", "the empress transformed"))
        got = repo.get_by_number(51)
        assert got is not None
        assert got.title == "Ais Wallenstein"
        assert "empress" in got.content

    def test_list_summaries_sorted_by_number(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        repo.add_many([_make(5), _make(2), _make(9)])
        nums = [s.number for s in repo.list_summaries()]
        assert nums == [2, 5, 9]

    def test_summary_does_not_carry_content(self, project_engine: Engine) -> None:
        # Listing should not need to load full content. We assert the summary
        # type structurally has no content attribute.
        repo = SqlAlchemyChapterRepository(project_engine)
        repo.add(_make(1))
        summary = repo.list_summaries()[0]
        assert not hasattr(summary, "content")

    def test_update_content_changes_status_and_modified(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        ch = repo.add(_make(1, "Old", "old body"))
        assert ch.id is not None
        updated = repo.update_content(ch.id, "New", "new body new body")
        assert updated.title == "New"
        assert updated.word_count == 4
        assert updated.status == ChapterStatus.MODIFIED


class TestSoftDelete:
    def test_soft_delete_hides_from_list(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        a = repo.add(_make(1, "A"))
        repo.add(_make(2, "B"))
        assert a.id is not None
        repo.soft_delete(a.id)
        nums = [s.number for s in repo.list_summaries()]
        assert nums == [2]

    def test_trash_lists_soft_deleted(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        ch = repo.add(_make(1, "A"))
        assert ch.id is not None
        repo.soft_delete(ch.id)
        trash = repo.list_trash()
        assert [t.number for t in trash] == [1]

    def test_restore_brings_back(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        ch = repo.add(_make(1, "A"))
        assert ch.id is not None
        repo.soft_delete(ch.id)
        restored = repo.restore(ch.id)
        assert restored.deleted_at is None
        assert [s.number for s in repo.list_summaries()] == [1]

    def test_partial_unique_allows_resurrection(self, project_engine: Engine) -> None:
        # After soft-deleting #1, we should be able to insert another #1
        # because the unique index is partial (deleted_at IS NULL).
        repo = SqlAlchemyChapterRepository(project_engine)
        first = repo.add(_make(1, "First"))
        assert first.id is not None
        repo.soft_delete(first.id)
        second = repo.add(_make(1, "Second take"))
        assert second.id != first.id
        active = repo.list_summaries()
        assert [s.title for s in active] == ["Second take"]

    def test_purge_deletes_only_old_records(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        old = repo.add(_make(1, "Old"))
        recent = repo.add(_make(2, "Recent"))
        assert old.id is not None and recent.id is not None
        # Manually backdate `old`'s deleted_at to 30 days ago.
        eight_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        with project_engine.begin() as conn:
            conn.execute(
                text("UPDATE chapters SET deleted_at = :d WHERE id = :id"),
                {"d": eight_days_ago, "id": old.id},
            )
        repo.soft_delete(recent.id)  # deleted "today"

        purged = repo.purge_expired(retention_days=7)
        assert purged == 1
        # `recent` still in trash; `old` is gone.
        trash_nums = {t.number for t in repo.list_trash()}
        assert trash_nums == {2}

    def test_purge_with_zero_retention(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        ch = repo.add(_make(1))
        assert ch.id is not None
        repo.soft_delete(ch.id)
        # Backdate by 1 second to be safely past 0-day retention.
        past = (datetime.now() - timedelta(seconds=1)).isoformat()
        with project_engine.begin() as conn:
            conn.execute(
                text("UPDATE chapters SET deleted_at = :d WHERE id = :id"),
                {"d": past, "id": ch.id},
            )
        assert repo.purge_expired(0) == 1

    def test_purge_negative_raises(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        with pytest.raises(ValueError):
            repo.purge_expired(-1)


class TestVersioning:
    def test_initial_extract_creates_version(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        ch = repo.add(_make(1, "Title", "first body"))
        assert ch.id is not None
        versions = repo.list_versions(ch.id)
        assert len(versions) == 1
        assert versions[0].edit_reason == EditReason.EXTRACT
        assert versions[0].valid_to is None  # current

    def test_update_creates_new_version_and_closes_old(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        ch = repo.add(_make(1, "Title", "first body"))
        assert ch.id is not None
        repo.update_content(ch.id, "Title", "second body changed")
        versions = repo.list_versions(ch.id)
        assert len(versions) == 2
        # Newest first
        assert versions[0].valid_to is None
        assert versions[0].edit_reason == EditReason.EDIT
        assert versions[1].valid_to is not None  # closed off

    def test_no_version_when_content_unchanged(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        ch = repo.add(_make(1, "Title", "same body"))
        assert ch.id is not None
        repo.update_content(ch.id, "Title", "same body")
        # Trigger only fires when title or content actually changes.
        assert len(repo.list_versions(ch.id)) == 1

    def test_restore_version_sets_content(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        ch = repo.add(_make(1, "Title", "first body"))
        assert ch.id is not None
        repo.update_content(ch.id, "Title", "second body")
        repo.update_content(ch.id, "Title", "third body")
        versions = repo.list_versions(ch.id)
        # versions[2] is the original (oldest).
        original = next(v for v in versions if v.edit_reason == EditReason.EXTRACT)
        repo.restore_version(original.id)
        current = repo.get_by_number(1)
        assert current is not None
        assert current.content == "first body"
        # Latest version should be marked as restore.
        latest = repo.list_versions(ch.id)[0]
        assert latest.edit_reason == EditReason.RESTORE

    def test_versions_capped_at_20(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        ch = repo.add(_make(1, "T", "v0"))
        assert ch.id is not None
        for i in range(1, 25):
            repo.update_content(ch.id, "T", f"v{i}")
        versions = repo.list_versions(ch.id)
        assert len(versions) == 20


class TestSearch:
    def test_finds_match_in_title(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        repo.add(_make(51, "Ais Wallenstein", "wind blew softly"))
        repo.add(_make(52, "The Good Cop", "where am I"))
        hits = repo.search("Wallenstein")
        assert len(hits) == 1
        assert hits[0].number == 51

    def test_finds_match_in_content(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        repo.add(_make(1, "T1", "the empress transformed into the wind"))
        repo.add(_make(2, "T2", "ais looked at lucian"))
        hits = repo.search("empress")
        assert len(hits) == 1
        assert hits[0].number == 1
        assert "empress" in hits[0].snippet.lower()

    def test_search_excludes_soft_deleted(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        ch = repo.add(_make(1, "Ais Wallenstein", "x"))
        assert ch.id is not None
        repo.soft_delete(ch.id)
        assert repo.search("Wallenstein") == []

    def test_empty_query_returns_empty(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        repo.add(_make(1, "T", "x"))
        assert repo.search("") == []
        assert repo.search("   ") == []

    def test_title_outranks_content(self, project_engine: Engine) -> None:
        repo = SqlAlchemyChapterRepository(project_engine)
        repo.add(_make(1, "winterheart", "summer breeze"))
        repo.add(_make(2, "summer story", "the word winterheart appears here"))
        hits = repo.search("winterheart")
        # Title weighted 2x via BM25 — chapter 1 (in title) ranks above chapter 2 (in body).
        assert [h.number for h in hits] == [1, 2]
