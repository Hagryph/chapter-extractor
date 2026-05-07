from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.viewmodels.project_list_vm import ProjectListViewModel  # noqa: E402


class TestProjectListViewModel:
    def test_initial_empty(self, qt_app, registry) -> None:
        del qt_app
        vm = ProjectListViewModel(registry)
        assert vm.projects == []

    def test_create_persists_and_emits(
        self, qt_app, qtbot, registry, tmp_path: Path
    ) -> None:
        del qt_app
        vm = ProjectListViewModel(registry)
        with qtbot.waitSignal(vm.project_created, timeout=1000):
            vm.create("Mine", tmp_path)
        assert len(vm.projects) == 1
        assert vm.projects[0].name == "Mine"

    def test_open_emits_project(
        self, qt_app, qtbot, registry, tmp_path: Path
    ) -> None:
        del qt_app
        vm = ProjectListViewModel(registry)
        vm.create("X", tmp_path)
        summary = vm.projects[0]
        with qtbot.waitSignal(vm.project_opened, timeout=1000) as blocker:
            vm.open(summary)
        opened = blocker.args[0]
        assert opened.name == "X"

    def test_delete_removes(self, qt_app, registry, tmp_path: Path) -> None:
        del qt_app
        vm = ProjectListViewModel(registry)
        vm.create("X", tmp_path)
        vm.delete(vm.projects[0])
        assert vm.projects == []

    def test_toggle_pin(self, qt_app, registry, tmp_path: Path) -> None:
        del qt_app
        vm = ProjectListViewModel(registry)
        vm.create("X", tmp_path)
        vm.toggle_pin(vm.projects[0])
        assert vm.projects[0].pinned is True
        vm.toggle_pin(vm.projects[0])
        assert vm.projects[0].pinned is False

    def test_project_at_bounds(self, qt_app, registry, tmp_path: Path) -> None:
        del qt_app
        vm = ProjectListViewModel(registry)
        vm.create("X", tmp_path)
        assert vm.project_at(0) is not None
        assert vm.project_at(99) is None
