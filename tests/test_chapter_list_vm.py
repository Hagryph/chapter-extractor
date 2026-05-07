from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.domain.enums import ChapterStatus  # noqa: E402
from chapter_extractor.domain.models import Chapter  # noqa: E402
from chapter_extractor.viewmodels.chapter_list_vm import ChapterListViewModel  # noqa: E402


def _chapter(number: int, title: str = "T") -> Chapter:
    ch = Chapter(
        number=number,
        title=title,
        content=f"body for {number}",
        filename=f"Chapter_{number:03d}.txt",
        file_path=Path(f"Chapter_{number:03d}.txt"),
        status=ChapterStatus.EXTRACTED,
        created_at=datetime.now(),
        modified_at=datetime.now(),
    )
    ch.recompute_word_count()
    return ch


class TestChapterListViewModel:
    def test_refresh_loads_summaries(self, qt_app, chapter_repo) -> None:
        del qt_app
        chapter_repo.add_many([_chapter(1), _chapter(2)])
        vm = ChapterListViewModel(chapter_repo)
        vm.refresh()
        assert vm.proxy_model.rowCount() == 2

    def test_select_by_proxy_row_emits(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        chapter_repo.add(_chapter(1, "First"))
        vm = ChapterListViewModel(chapter_repo)
        vm.refresh()
        with qtbot.waitSignal(vm.selection_changed, timeout=1000) as blocker:
            vm.select_by_proxy_row(0)
        summary = blocker.args[0]
        assert summary.title == "First"
        assert vm.selected_chapter_id == summary.id

    def test_search_filters(self, qt_app, chapter_repo) -> None:
        del qt_app
        chapter_repo.add_many([_chapter(1, "Ais"), _chapter(2, "Other")])
        vm = ChapterListViewModel(chapter_repo)
        vm.refresh()
        vm.set_search("ais")
        assert vm.proxy_model.rowCount() == 1

    def test_add_extracted_chapters_persists_and_refreshes(
        self, qt_app, chapter_repo
    ) -> None:
        del qt_app
        vm = ChapterListViewModel(chapter_repo)
        added = vm.add_extracted_chapters([_chapter(1), _chapter(2)])
        assert all(ch.id is not None for ch in added)
        assert vm.proxy_model.rowCount() == 2

    def test_soft_delete_selected_clears_selection(
        self, qt_app, qtbot, chapter_repo
    ) -> None:
        del qt_app
        chapter_repo.add(_chapter(1))
        vm = ChapterListViewModel(chapter_repo)
        vm.refresh()
        vm.select_by_proxy_row(0)
        with qtbot.waitSignal(vm.chapter_soft_deleted, timeout=1000):
            vm.soft_delete_selected()
        assert vm.proxy_model.rowCount() == 0
        assert vm.selected_chapter_id is None

    def test_select_invalid_row_clears_selection(
        self, qt_app, qtbot, chapter_repo
    ) -> None:
        del qt_app
        chapter_repo.add(_chapter(1))
        vm = ChapterListViewModel(chapter_repo)
        vm.refresh()
        vm.select_by_proxy_row(0)
        with qtbot.waitSignal(vm.selection_changed, timeout=1000) as blocker:
            vm.select_by_proxy_row(999)
        assert blocker.args[0] is None
        assert vm.selected_chapter_id is None

    def test_select_by_id_unknown_clears_selection(self, qt_app, chapter_repo) -> None:
        del qt_app
        chapter_repo.add(_chapter(1))
        vm = ChapterListViewModel(chapter_repo)
        vm.refresh()
        vm.select_by_id(99999)
        assert vm.selected_chapter_id is None
