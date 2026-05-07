from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine

from chapter_extractor.services.db.engine import SqliteEngineFactory
from chapter_extractor.services.db.migrator import (
    project_migrator,
    registry_migrator,
)


@pytest.fixture
def project_engine() -> Iterator[Engine]:
    engine = SqliteEngineFactory.in_memory()
    project_migrator().apply_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def registry_engine() -> Iterator[Engine]:
    engine = SqliteEngineFactory.in_memory()
    registry_migrator().apply_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def qt_app():
    """Single QApplication for the whole test session."""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def chapter_repo(project_engine: Engine):
    from chapter_extractor.services.db.chapter_repo import SqlAlchemyChapterRepository

    return SqlAlchemyChapterRepository(project_engine)


@pytest.fixture
def registry(registry_engine: Engine):
    from chapter_extractor.services.db.registry_repo import SqlAlchemyRegistry

    return SqlAlchemyRegistry(registry_engine)
