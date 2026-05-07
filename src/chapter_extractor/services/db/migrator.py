from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Engine

from chapter_extractor.services.db.engine import ConnectionHelper
from chapter_extractor.services.db.orm_base import ProjectBase, RegistryBase
from chapter_extractor.services.db.tables_project import PROJECT_RAW_DDL
from chapter_extractor.services.db.tables_registry import REGISTRY_RAW_DDL


@dataclass(frozen=True, slots=True)
class Migration:
    target_version: int
    apply: Callable[[Engine], None]


class SchemaMigrator:
    """Forward-only migrations gated by PRAGMA user_version.

    Each Migration is idempotent and runs only if the DB is below its target.
    The base v1 migration creates the full schema via SQLAlchemy metadata
    plus raw DDL for things SQLAlchemy can't model (FTS5, partial indexes,
    triggers, views).
    """

    def __init__(self, migrations: list[Migration]) -> None:
        self._migrations = sorted(migrations, key=lambda m: m.target_version)

    def apply_all(self, engine: Engine) -> int:
        applied_count = 0
        with engine.connect() as conn:
            helper = ConnectionHelper(conn)
            current = helper.user_version()
        for mig in self._migrations:
            if mig.target_version > current:
                mig.apply(engine)
                with engine.begin() as conn:
                    ConnectionHelper(conn).set_user_version(mig.target_version)
                current = mig.target_version
                applied_count += 1
        return applied_count


def _v1_project_schema(engine: Engine) -> None:
    ProjectBase.metadata.create_all(engine)
    with engine.begin() as conn:
        ConnectionHelper(conn).executescript(PROJECT_RAW_DDL)


def _v1_registry_schema(engine: Engine) -> None:
    RegistryBase.metadata.create_all(engine)
    with engine.begin() as conn:
        ConnectionHelper(conn).executescript(REGISTRY_RAW_DDL)


def project_migrator() -> SchemaMigrator:
    return SchemaMigrator([Migration(target_version=1, apply=_v1_project_schema)])


def registry_migrator() -> SchemaMigrator:
    return SchemaMigrator([Migration(target_version=1, apply=_v1_registry_schema)])
