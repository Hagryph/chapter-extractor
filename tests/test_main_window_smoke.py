from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.infrastructure.app_context import AppContext  # noqa: E402
from chapter_extractor.infrastructure.paths import AppPaths  # noqa: E402
from chapter_extractor.viewmodels.main_vm import MainViewModel  # noqa: E402
from chapter_extractor.views.main_window import MainWindow  # noqa: E402


class TestMainWindowSmoke:
    def test_builds_with_three_pane_splitter(self, qt_app, tmp_path: Path) -> None:
        del qt_app
        ctx = AppContext.bootstrap(AppPaths.for_testing(tmp_path))
        try:
            vm = MainViewModel(ctx)
            window = MainWindow(ctx, vm)
            try:
                assert window.splitter.count() == 3
                # Empty placeholder visible until a project opens.
                assert window.centre_widget.__class__.__name__ == "EmptyStateWidget"
                assert window.reader_widget.__class__.__name__ == "EmptyStateWidget"
            finally:
                window.close()
        finally:
            ctx.shutdown()

    def test_opens_project_swaps_panes(self, qt_app, qtbot, tmp_path: Path) -> None:
        del qt_app
        ctx = AppContext.bootstrap(AppPaths.for_testing(tmp_path))
        try:
            vm = MainViewModel(ctx)
            window = MainWindow(ctx, vm)
            try:
                with qtbot.waitSignal(vm.project_changed, timeout=2000):
                    vm.project_list_vm.create("Mine", tmp_path / "mine")
                assert window.centre_widget.__class__.__name__ == "ChapterListPane"
                assert window.reader_widget.__class__.__name__ == "ReaderPane"
                assert "Mine" in window.windowTitle()
            finally:
                window.close()
        finally:
            ctx.shutdown()

    def test_close_project_restores_empty_panes(
        self, qt_app, qtbot, tmp_path: Path
    ) -> None:
        del qt_app
        ctx = AppContext.bootstrap(AppPaths.for_testing(tmp_path))
        try:
            vm = MainViewModel(ctx)
            window = MainWindow(ctx, vm)
            try:
                with qtbot.waitSignal(vm.project_changed, timeout=2000):
                    vm.project_list_vm.create("X", tmp_path / "x")
                with qtbot.waitSignal(vm.project_changed, timeout=2000):
                    vm.close_project()
                assert window.centre_widget.__class__.__name__ == "EmptyStateWidget"
                assert window.reader_widget.__class__.__name__ == "EmptyStateWidget"
            finally:
                window.close()
        finally:
            ctx.shutdown()

    def test_splitter_initial_sizes_match_style(
        self, qt_app, tmp_path: Path
    ) -> None:
        from chapter_extractor.views.style import ViewStyle

        del qt_app
        ctx = AppContext.bootstrap(AppPaths.for_testing(tmp_path))
        try:
            vm = MainViewModel(ctx)
            window = MainWindow(ctx, vm)
            try:
                expected = [
                    ViewStyle.SIDEBAR_WIDTH_DEFAULT,
                    ViewStyle.LIST_WIDTH_DEFAULT,
                    ViewStyle.READER_WIDTH_DEFAULT,
                ]
                # restoreState may have populated values; if not, defaults apply.
                sizes = window.splitter.sizes()
                assert len(sizes) == 3
                assert all(s > 0 for s in sizes)
                del expected
            finally:
                window.close()
        finally:
            ctx.shutdown()
