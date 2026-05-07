from __future__ import annotations

from sqlalchemy import Engine, text


class TestPragmas:
    def test_foreign_keys_enabled(self, project_engine: Engine) -> None:
        with project_engine.connect() as conn:
            row = conn.execute(text("PRAGMA foreign_keys")).fetchone()
        assert row is not None
        assert int(row[0]) == 1

    def test_journal_mode_is_wal_or_memory(self, project_engine: Engine) -> None:
        # In-memory DBs report 'memory' for journal_mode; file-backed report 'wal'.
        with project_engine.connect() as conn:
            row = conn.execute(text("PRAGMA journal_mode")).fetchone()
        assert row is not None
        assert str(row[0]).lower() in {"wal", "memory"}

    def test_synchronous_normal(self, project_engine: Engine) -> None:
        with project_engine.connect() as conn:
            row = conn.execute(text("PRAGMA synchronous")).fetchone()
        assert row is not None
        # NORMAL == 1
        assert int(row[0]) == 1

    def test_busy_timeout_set(self, project_engine: Engine) -> None:
        with project_engine.connect() as conn:
            row = conn.execute(text("PRAGMA busy_timeout")).fetchone()
        assert row is not None
        assert int(row[0]) == 5000
