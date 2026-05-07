from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import Connection
from sqlalchemy.pool import StaticPool


class SqliteEngineFactory:
    """Builds SQLAlchemy engines configured for SQLite production use.

    Pragmas applied on every connection (per
    https://www.sqlite.org/pragma.html and
    https://sqlite.org/wal.html):
      - journal_mode=WAL        : best concurrency for single-writer apps
      - synchronous=NORMAL      : balanced durability/perf with WAL
      - foreign_keys=ON         : enforce FK constraints (off by default!)
      - busy_timeout=5000       : avoid spurious "database is locked" errors
      - temp_store=MEMORY       : faster temp tables/indexes
      - cache_size=-16000       : 16 MiB negative = KiB
    """

    @classmethod
    def for_file(cls, db_path: Path, *, echo: bool = False) -> Engine:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{db_path.as_posix()}"
        engine = create_engine(url, echo=echo, future=True)
        cls._attach_pragmas(engine)
        return engine

    @classmethod
    def in_memory(cls, *, echo: bool = False) -> Engine:
        """Shared in-memory engine for tests. StaticPool keeps a single connection
        alive so the schema persists across sessions in the same test."""
        engine = create_engine(
            "sqlite://",
            echo=echo,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls._attach_pragmas(engine)
        return engine

    @staticmethod
    def _attach_pragmas(engine: Engine) -> None:
        @event.listens_for(engine, "connect")
        def _on_connect(dbapi_conn, connection_record):  # type: ignore[no-untyped-def]
            del connection_record
            cur = dbapi_conn.cursor()
            try:
                cur.execute("PRAGMA journal_mode = WAL")
                cur.execute("PRAGMA synchronous = NORMAL")
                cur.execute("PRAGMA foreign_keys = ON")
                cur.execute("PRAGMA busy_timeout = 5000")
                cur.execute("PRAGMA temp_store = MEMORY")
                cur.execute("PRAGMA cache_size = -16000")
            finally:
                cur.close()


class ConnectionHelper:
    """Convenience wrapper for raw DDL execution (FTS5, triggers, partial indexes
    that SQLAlchemy can't model declaratively)."""

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def executescript(self, script: str) -> None:
        # Use the underlying sqlite3 driver's executescript, which correctly
        # handles `;` inside trigger bodies (a naive split-on-semicolon breaks
        # CREATE TRIGGER ... BEGIN ...; END statements).
        raw = self._conn.connection.driver_connection
        raw.executescript(script)

    def user_version(self) -> int:
        row = self._conn.exec_driver_sql("PRAGMA user_version").fetchone()
        return int(row[0]) if row else 0

    def set_user_version(self, version: int) -> None:
        self._conn.exec_driver_sql(f"PRAGMA user_version = {int(version)}")
