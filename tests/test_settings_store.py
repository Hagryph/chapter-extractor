from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from sqlalchemy import Engine  # noqa: E402

from chapter_extractor.domain.enums import ThemeMode  # noqa: E402
from chapter_extractor.infrastructure.settings import SettingsStore  # noqa: E402
from chapter_extractor.services.db.registry_repo import SqlAlchemyRegistry  # noqa: E402


@pytest.fixture(scope="module")
def qt_app():
    """Single QApplication for all tests in this module."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


class TestSettingsStore:
    def test_loads_initial_state_from_registry(
        self, qt_app, registry_engine: Engine
    ) -> None:
        del qt_app
        registry = SqlAlchemyRegistry(registry_engine)
        store = SettingsStore(registry)
        assert store.theme_mode == ThemeMode.AUTO
        assert store.retention_days == 7

    def test_set_theme_persists_and_emits(self, qt_app, registry_engine: Engine) -> None:
        del qt_app
        registry = SqlAlchemyRegistry(registry_engine)
        store = SettingsStore(registry)
        captured: list[ThemeMode] = []
        store.theme_changed.connect(captured.append)

        store.set_theme_mode(ThemeMode.DARK)

        assert captured == [ThemeMode.DARK]
        assert registry.get_app_settings().theme_mode == ThemeMode.DARK

    def test_setting_same_value_does_not_emit(
        self, qt_app, registry_engine: Engine
    ) -> None:
        del qt_app
        registry = SqlAlchemyRegistry(registry_engine)
        store = SettingsStore(registry)
        captured: list[ThemeMode] = []
        store.theme_changed.connect(captured.append)

        store.set_theme_mode(ThemeMode.AUTO)  # already AUTO

        assert captured == []

    def test_set_retention_negative_raises(
        self, qt_app, registry_engine: Engine
    ) -> None:
        del qt_app
        registry = SqlAlchemyRegistry(registry_engine)
        store = SettingsStore(registry)
        with pytest.raises(ValueError):
            store.set_retention_days(-1)

    def test_set_retention_emits_and_persists(
        self, qt_app, registry_engine: Engine
    ) -> None:
        del qt_app
        registry = SqlAlchemyRegistry(registry_engine)
        store = SettingsStore(registry)
        captured: list[int] = []
        store.retention_changed.connect(captured.append)

        store.set_retention_days(14)

        assert captured == [14]
        assert registry.get_app_settings().soft_delete_retention_days == 14
