from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Engine

from chapter_extractor.domain.enums import ThemeMode
from chapter_extractor.domain.models import Project, ProjectSettings
from chapter_extractor.services.db.project_repo import SqlAlchemyProjectRepository


class TestProjectRepo:
    def test_create_then_load_roundtrip(self, project_engine: Engine, tmp_path: Path) -> None:
        repo = SqlAlchemyProjectRepository(project_engine, tmp_path)
        proj = Project(
            name="My Novel",
            root_path=tmp_path,
            settings=ProjectSettings(font_size=18, theme_mode=ThemeMode.DARK),
        )
        repo.create(proj)
        loaded = repo.load(tmp_path)
        assert loaded.name == "My Novel"
        assert loaded.settings.font_size == 18
        assert loaded.settings.theme_mode == ThemeMode.DARK

    def test_create_twice_raises(self, project_engine: Engine, tmp_path: Path) -> None:
        repo = SqlAlchemyProjectRepository(project_engine, tmp_path)
        proj = Project(name="X", root_path=tmp_path)
        repo.create(proj)
        with pytest.raises(RuntimeError):
            repo.create(proj)

    def test_update_settings_persists(self, project_engine: Engine, tmp_path: Path) -> None:
        repo = SqlAlchemyProjectRepository(project_engine, tmp_path)
        proj = Project(name="X", root_path=tmp_path)
        repo.create(proj)
        proj.settings.font_size = 22
        proj.settings.column_width = 80
        repo.update_settings(proj)

        loaded = repo.load(tmp_path)
        assert loaded.settings.font_size == 22
        assert loaded.settings.column_width == 80
