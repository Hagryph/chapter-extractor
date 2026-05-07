from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.domain.enums import ViewMode  # noqa: E402
from chapter_extractor.infrastructure.app_context import AppContext  # noqa: E402
from chapter_extractor.infrastructure.paths import AppPaths  # noqa: E402
from chapter_extractor.viewmodels.main_vm import MainViewModel  # noqa: E402
from chapter_extractor.views.main_window import MainWindow  # noqa: E402


class TestFocusMode:
    def test_focus_hides_sidebar_and_list(
        self, qt_app, qtbot, tmp_path: Path
    ) -> None:
        del qt_app
        ctx = AppContext.bootstrap(AppPaths.for_testing(tmp_path))
        try:
            vm = MainViewModel(ctx)
            window = MainWindow(ctx, vm)
            try:
                qtbot.addWidget(window)
                with qtbot.waitSignal(vm.project_changed, timeout=2000):
                    vm.project_list_vm.create("X", tmp_path / "x")

                vm.reader_vm.set_view_mode(ViewMode.FOCUS)
                assert not window.sidebar.isVisible() or window.sidebar.isHidden()
            finally:
                window.close()
        finally:
            ctx.shutdown()

    def test_exit_to_default_restores_panes(
        self, qt_app, qtbot, tmp_path: Path
    ) -> None:
        del qt_app
        ctx = AppContext.bootstrap(AppPaths.for_testing(tmp_path))
        try:
            vm = MainViewModel(ctx)
            window = MainWindow(ctx, vm)
            try:
                qtbot.addWidget(window)
                with qtbot.waitSignal(vm.project_changed, timeout=2000):
                    vm.project_list_vm.create("X", tmp_path / "x")

                vm.reader_vm.set_view_mode(ViewMode.FOCUS)
                vm.reader_vm.exit_to_default()
                window.show()
                # After exit_to_default, sidebar reappears (DEFAULT mode).
                assert vm.reader_vm.view_mode == ViewMode.DEFAULT
            finally:
                window.close()
        finally:
            ctx.shutdown()


class TestPopOutWiring:
    def test_pop_out_opens_window(self, qt_app, qtbot, tmp_path: Path) -> None:
        from datetime import datetime

        from chapter_extractor.domain.enums import ChapterStatus
        from chapter_extractor.domain.models import Chapter

        del qt_app
        ctx = AppContext.bootstrap(AppPaths.for_testing(tmp_path))
        try:
            vm = MainViewModel(ctx)
            window = MainWindow(ctx, vm)
            try:
                qtbot.addWidget(window)
                with qtbot.waitSignal(vm.project_changed, timeout=2000):
                    vm.project_list_vm.create("X", tmp_path / "x")

                ch = Chapter(
                    number=1,
                    title="T",
                    content="hello",
                    filename="x.txt",
                    file_path=Path("x.txt"),
                    status=ChapterStatus.EXTRACTED,
                    word_count=1,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                )
                vm.chapter_list_vm.add_extracted_chapters([ch])
                vm.chapter_list_vm.select_by_proxy_row(0)

                # Trigger pop-out
                wm = window.window_manager
                assert wm is not None
                vm.reader_vm.pop_out()
                # The chapter id was assigned by add_many; query it.
                summary = vm.chapter_list_vm.source_model.summary_at(0)
                assert wm.is_open(summary.id)
            finally:
                window.close()
        finally:
            ctx.shutdown()
