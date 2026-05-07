from __future__ import annotations

from sqlalchemy import Engine

from chapter_extractor.domain.enums import ThemeMode
from chapter_extractor.domain.models import AppSettings
from chapter_extractor.services.db.registry_repo import SqlAlchemyRegistry


class TestRegistryAppSettings:
    def test_default_settings_present_after_init(self, registry_engine: Engine) -> None:
        reg = SqlAlchemyRegistry(registry_engine)
        s = reg.get_app_settings()
        assert s.theme_mode == ThemeMode.AUTO
        assert s.last_project_id is None
        assert s.soft_delete_retention_days == 7

    def test_update_persists(self, registry_engine: Engine, tmp_path) -> None:
        reg = SqlAlchemyRegistry(registry_engine)
        # last_project_id has a FK to projects(id); register a project so the
        # FK resolves.
        from chapter_extractor.domain.models import Project

        proj = reg.register(Project(name="X", root_path=tmp_path))
        new = AppSettings(
            theme_mode=ThemeMode.DARK,
            last_project_id=proj.id,
            soft_delete_retention_days=14,
        )
        reg.update_app_settings(new)
        loaded = reg.get_app_settings()
        assert loaded.theme_mode == ThemeMode.DARK
        assert loaded.last_project_id == proj.id
        assert loaded.soft_delete_retention_days == 14

    def test_unknown_theme_falls_back_to_auto(self, registry_engine: Engine) -> None:
        # If the row somehow contains an invalid theme value, get_app_settings
        # should not raise — it returns AUTO.
        from sqlalchemy import text

        reg = SqlAlchemyRegistry(registry_engine)
        with registry_engine.begin() as conn:
            conn.execute(text("UPDATE app_settings SET theme_mode = 'badvalue' WHERE id = 1"))
        s = reg.get_app_settings()
        assert s.theme_mode == ThemeMode.AUTO
