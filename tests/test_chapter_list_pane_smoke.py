from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.domain.enums import ChapterStatus  # noqa: E402
from chapter_extractor.domain.models import Chapter  # noqa: E402
from chapter_extractor.viewmodels.chapter_list_vm import ChapterListViewModel  # noqa: E402
from chapter_extractor.views.chapter_list_pane import ChapterListPane  # noqa: E402


def _ch(n: int, title: str = "T") -> Chapter:
    ch = Chapter(
        number=n,
        title=title,
        content="x",
        filename=f"Chapter_{n:03d}.txt",
        file_path=Path(f"Chapter_{n:03d}.txt"),
        status=ChapterStatus.EXTRACTED,
        created_at=datetime.now(),
        modified_at=datetime.now(),
    )
    ch.recompute_word_count()
    return ch


class TestChapterListPaneSmoke:
    def test_builds_and_binds_proxy(self, qt_app, chapter_repo) -> None:
        del qt_app
        chapter_repo.add_many([_ch(1, "First"), _ch(2, "Second")])
        vm = ChapterListViewModel(chapter_repo)
        vm.refresh()
        pane = ChapterListPane(vm)
        try:
            assert pane.list_view.model() is vm.proxy_model
            assert vm.proxy_model.rowCount() == 2
        finally:
            pane.deleteLater()

    def test_search_filters_proxy(self, qt_app, chapter_repo) -> None:
        del qt_app
        chapter_repo.add_many([_ch(1, "Ais"), _ch(2, "Other")])
        vm = ChapterListViewModel(chapter_repo)
        vm.refresh()
        pane = ChapterListPane(vm)
        try:
            pane.search_box.setText("ais")
            assert vm.proxy_model.rowCount() == 1
        finally:
            pane.deleteLater()

    def test_selection_drives_vm(
        self, qt_app, qtbot, chapter_repo
    ) -> None:
        del qt_app
        chapter_repo.add(_ch(1, "First"))
        vm = ChapterListViewModel(chapter_repo)
        vm.refresh()
        pane = ChapterListPane(vm)
        try:
            with qtbot.waitSignal(vm.selection_changed, timeout=1000):
                idx = vm.proxy_model.index(0, 0)
                pane.list_view.setCurrentIndex(idx)
            assert vm.selected_chapter_id is not None
        finally:
            pane.deleteLater()
