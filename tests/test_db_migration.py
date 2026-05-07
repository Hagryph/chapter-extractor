from __future__ import annotations

from sqlalchemy import Engine, text

from chapter_extractor.services.db.engine import SqliteEngineFactory
from chapter_extractor.services.db.migrator import (
    project_migrator,
    registry_migrator,
)


class TestProjectMigration:
    def test_user_version_set_to_1(self, project_engine: Engine) -> None:
        with project_engine.connect() as conn:
            row = conn.execute(text("PRAGMA user_version")).fetchone()
        assert row is not None
        assert int(row[0]) == 1

    def test_re_running_is_idempotent(self) -> None:
        engine = SqliteEngineFactory.in_memory()
        first = project_migrator().apply_all(engine)
        second = project_migrator().apply_all(engine)
        assert first == 1
        assert second == 0
        engine.dispose()

    def test_all_expected_tables_exist(self, project_engine: Engine) -> None:
        with project_engine.connect() as conn:
            rows = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        names = {r[0] for r in rows}
        # virtual table also stored under chapters_fts; with FTS5 it creates
        # backing _data, _idx, _content, _docsize, _config tables.
        assert "project_meta" in names
        assert "chapters" in names
        assert "chapter_versions" in names
        assert "chapters_fts" in names

    def test_views_exist(self, project_engine: Engine) -> None:
        with project_engine.connect() as conn:
            rows = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='view'")
            ).fetchall()
        names = {r[0] for r in rows}
        assert "v_chapter_summary" in names
        assert "v_chapter_trash" in names

    def test_partial_unique_index_on_chapter_number(self, project_engine: Engine) -> None:
        with project_engine.connect() as conn:
            rows = conn.execute(
                text("SELECT name, sql FROM sqlite_master WHERE type='index' AND name='uq_chapters_number_active'")
            ).fetchall()
        assert len(rows) == 1
        assert "deleted_at IS NULL" in rows[0][1]


class TestRegistryMigration:
    def test_tables_exist(self, registry_engine: Engine) -> None:
        with registry_engine.connect() as conn:
            rows = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        names = {r[0] for r in rows}
        assert "projects" in names
        assert "app_settings" in names

    def test_recent_view_exists(self, registry_engine: Engine) -> None:
        with registry_engine.connect() as conn:
            rows = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='view' AND name='v_recent_projects'")
            ).fetchall()
        assert len(rows) == 1

    def test_re_running_is_idempotent(self) -> None:
        engine = SqliteEngineFactory.in_memory()
        first = registry_migrator().apply_all(engine)
        second = registry_migrator().apply_all(engine)
        assert first == 1
        assert second == 0
        engine.dispose()
