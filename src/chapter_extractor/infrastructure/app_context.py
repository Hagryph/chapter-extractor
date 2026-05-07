from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine

from chapter_extractor.infrastructure.clipboard import QtClipboard
from chapter_extractor.infrastructure.paths import AppPaths
from chapter_extractor.infrastructure.settings import SettingsStore
from chapter_extractor.services.db.engine import SqliteEngineFactory
from chapter_extractor.services.db.migrator import registry_migrator
from chapter_extractor.services.db.registry_repo import SqlAlchemyRegistry


@dataclass
class AppContext:
    """Composition root. Wires up the cross-cutting infrastructure.

    Per-project services (chapter repo, project repo, cleanup scheduler) are
    bound later via `bind_project()` once the user opens a project.
    """

    paths: AppPaths
    registry_engine: Engine
    registry: SqlAlchemyRegistry
    settings: SettingsStore
    clipboard: QtClipboard

    @classmethod
    def bootstrap(cls, paths: AppPaths | None = None) -> AppContext:
        paths = paths or AppPaths.default()
        paths.ensure_dirs()

        registry_engine = SqliteEngineFactory.for_file(paths.registry_db_path)
        registry_migrator().apply_all(registry_engine)

        registry = SqlAlchemyRegistry(registry_engine)
        settings = SettingsStore(registry)
        clipboard = QtClipboard()

        return cls(
            paths=paths,
            registry_engine=registry_engine,
            registry=registry,
            settings=settings,
            clipboard=clipboard,
        )

    def shutdown(self) -> None:
        self.registry_engine.dispose()
