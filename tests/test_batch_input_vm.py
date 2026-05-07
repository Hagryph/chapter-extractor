from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.services.parser import ChapterParser  # noqa: E402
from chapter_extractor.viewmodels.batch_input_vm import BatchInputViewModel  # noqa: E402

BATCH_TEXT = """Chapter 1: First
body of one
. . .
Chapter 2: Second
body of two
"""


class TestBatchInputViewModel:
    def test_preview_returns_parse_result(self, qt_app, chapter_repo) -> None:
        del qt_app
        vm = BatchInputViewModel(ChapterParser(), chapter_repo)
        result = vm.preview(BATCH_TEXT)
        assert [c.number for c in result.chapters] == [1, 2]

    def test_preview_emits(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        vm = BatchInputViewModel(ChapterParser(), chapter_repo)
        with qtbot.waitSignal(vm.preview_changed, timeout=1000) as blocker:
            vm.preview(BATCH_TEXT)
        assert len(blocker.args[0].chapters) == 2

    def test_commit_persists_and_emits(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        vm = BatchInputViewModel(ChapterParser(), chapter_repo)
        with qtbot.waitSignal(vm.commit_succeeded, timeout=1000) as blocker:
            vm.commit(BATCH_TEXT)
        assert blocker.args[0] == 2
        assert len(chapter_repo.list_summaries()) == 2

    def test_commit_with_no_headers_emits_failed(
        self, qt_app, qtbot, chapter_repo
    ) -> None:
        del qt_app
        vm = BatchInputViewModel(ChapterParser(), chapter_repo)
        with qtbot.waitSignal(vm.commit_failed, timeout=1000) as blocker:
            added = vm.commit("no chapter markers here at all")
        assert added == []
        assert "No chapter headers" in blocker.args[0]
