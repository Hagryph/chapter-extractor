from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.infrastructure.app_context import AppContext  # noqa: E402
from chapter_extractor.infrastructure.paths import AppPaths  # noqa: E402
from chapter_extractor.viewmodels.main_vm import MainViewModel  # noqa: E402


class TestMainViewModel:
    def test_no_project_initially(self, qt_app, tmp_path: Path) -> None:
        del qt_app
        ctx = AppContext.bootstrap(AppPaths.for_testing(tmp_path))
        try:
            vm = MainViewModel(ctx)
            assert vm.current_project is None
            assert vm.chapter_list_vm is None
        finally:
            ctx.shutdown()

    def test_create_then_open_project(self, qt_app, qtbot, tmp_path: Path) -> None:
        del qt_app
        ctx = AppContext.bootstrap(AppPaths.for_testing(tmp_path))
        try:
            vm = MainViewModel(ctx)
            project_root = tmp_path / "documents" / "ChapterExtractor" / "Mine"
            with qtbot.waitSignal(vm.project_changed, timeout=2000):
                vm.project_list_vm.create("Mine", project_root)
            assert vm.current_project is not None
            assert vm.current_project.name == "Mine"
            assert vm.chapter_list_vm is not None
            assert vm.reader_vm is not None
            assert vm.batch_input_vm is not None
        finally:
            ctx.shutdown()

    def test_close_project_tears_down(self, qt_app, qtbot, tmp_path: Path) -> None:
        del qt_app
        ctx = AppContext.bootstrap(AppPaths.for_testing(tmp_path))
        try:
            vm = MainViewModel(ctx)
            with qtbot.waitSignal(vm.project_changed, timeout=2000):
                vm.project_list_vm.create("X", tmp_path / "x")
            with qtbot.waitSignal(vm.project_changed, timeout=2000):
                vm.close_project()
            assert vm.current_project is None
            assert vm.chapter_list_vm is None
        finally:
            ctx.shutdown()
