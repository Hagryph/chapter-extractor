from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Engine

from chapter_extractor.domain.models import Project
from chapter_extractor.services.db.registry_repo import SqlAlchemyRegistry


class TestRegistry:
    def test_register_returns_summary_with_id(self, registry_engine: Engine, tmp_path: Path) -> None:
        reg = SqlAlchemyRegistry(registry_engine)
        summary = reg.register(Project(name="A", root_path=tmp_path))
        assert summary.id > 0
        assert summary.name == "A"

    def test_list_recent_pinned_first(self, registry_engine: Engine, tmp_path: Path) -> None:
        reg = SqlAlchemyRegistry(registry_engine)
        a = reg.register(Project(name="A", root_path=tmp_path / "a"))
        b = reg.register(Project(name="B", root_path=tmp_path / "b"))
        reg.set_pinned(b.id, True)
        listed = reg.list_projects()
        assert [p.name for p in listed] == ["B", "A"]
        del a

    def test_register_existing_path_updates_in_place(self, registry_engine: Engine, tmp_path: Path) -> None:
        reg = SqlAlchemyRegistry(registry_engine)
        first = reg.register(Project(name="Old", root_path=tmp_path))
        second = reg.register(Project(name="Renamed", root_path=tmp_path))
        assert first.id == second.id
        assert second.name == "Renamed"
        assert len(reg.list_projects()) == 1

    def test_unregister_removes(self, registry_engine: Engine, tmp_path: Path) -> None:
        reg = SqlAlchemyRegistry(registry_engine)
        s = reg.register(Project(name="X", root_path=tmp_path))
        reg.unregister(s.id)
        assert reg.list_projects() == []

    def test_unregister_unknown_raises(self, registry_engine: Engine) -> None:
        reg = SqlAlchemyRegistry(registry_engine)
        with pytest.raises(KeyError):
            reg.unregister(9999)

    def test_touch_last_opened_changes_value(self, registry_engine: Engine, tmp_path: Path) -> None:
        reg = SqlAlchemyRegistry(registry_engine)
        s = reg.register(Project(name="X", root_path=tmp_path))
        before = s.last_opened_at
        reg.touch_last_opened(s.id)
        after = reg.list_projects()[0].last_opened_at
        assert after is not None
        assert before is None or after >= before
