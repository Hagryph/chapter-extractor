from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.domain.enums import ChapterStatus, ColumnWidth, ViewMode  # noqa: E402
from chapter_extractor.domain.models import Chapter  # noqa: E402
from chapter_extractor.viewmodels.reader_vm import ReaderViewModel  # noqa: E402


class FakeClipboard:
    def __init__(self) -> None:
        self.text: str | None = None

    def copy(self, text: str) -> None:
        self.text = text


def _ch(number: int, body: str = "x" * 5) -> Chapter:
    ch = Chapter(
        number=number,
        title=f"T{number}",
        content=body,
        filename=f"Chapter_{number:03d}.txt",
        file_path=Path(f"Chapter_{number:03d}.txt"),
        status=ChapterStatus.EXTRACTED,
        created_at=datetime.now(),
        modified_at=datetime.now(),
    )
    ch.recompute_word_count()
    return ch


class TestReaderViewModel:
    def test_initial_state(self, qt_app, chapter_repo) -> None:
        del qt_app
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        assert vm.chapter is None
        assert vm.view_mode == ViewMode.DEFAULT
        assert vm.font_size == 16
        assert vm.column_width == ColumnWidth.OPTIMAL

    def test_load_chapter_emits(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        added = chapter_repo.add(_ch(1, "hello world"))
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        with qtbot.waitSignal(vm.chapter_loaded, timeout=1000) as blocker:
            vm.load_chapter(added.id)
        loaded = blocker.args[0]
        assert loaded.number == 1

    def test_load_none_clears_chapter(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        added = chapter_repo.add(_ch(1))
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        vm.load_chapter(added.id)
        with qtbot.waitSignal(vm.chapter_loaded, timeout=1000) as blocker:
            vm.load_chapter(None)
        assert blocker.args[0] is None

    def test_copy_uses_clipboard(self, qt_app, chapter_repo) -> None:
        del qt_app
        added = chapter_repo.add(_ch(1, "the body"))
        clip = FakeClipboard()
        vm = ReaderViewModel(chapter_repo, clip)
        vm.load_chapter(added.id)
        vm.copy_current_content()
        assert clip.text is not None
        assert "the body" in clip.text

    def test_copy_no_chapter_is_safe(self, qt_app, chapter_repo) -> None:
        del qt_app
        clip = FakeClipboard()
        vm = ReaderViewModel(chapter_repo, clip)
        vm.copy_current_content()
        assert clip.text is None

    def test_view_mode_cycle(self, qt_app, chapter_repo) -> None:
        del qt_app
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        emitted: list[ViewMode] = []
        vm.view_mode_changed.connect(emitted.append)
        vm.cycle_view_mode()
        vm.cycle_view_mode()
        vm.cycle_view_mode()
        assert emitted == [ViewMode.FOCUS, ViewMode.DISTRACTION_FREE, ViewMode.DEFAULT]

    def test_set_view_mode_no_op_when_same(self, qt_app, chapter_repo) -> None:
        del qt_app
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        emitted: list[ViewMode] = []
        vm.view_mode_changed.connect(emitted.append)
        vm.set_view_mode(ViewMode.DEFAULT)
        assert emitted == []

    def test_font_size_clamps(self, qt_app, chapter_repo) -> None:
        del qt_app
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        vm.set_font_size(2)
        assert vm.font_size == ReaderViewModel.MIN_FONT_SIZE
        vm.set_font_size(99)
        assert vm.font_size == ReaderViewModel.MAX_FONT_SIZE

    def test_adjust_font_size(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        with qtbot.waitSignal(vm.typography_changed, timeout=1000):
            vm.adjust_font_size(2)
        assert vm.font_size == 18

    def test_line_spacing_clamps(self, qt_app, chapter_repo) -> None:
        del qt_app
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        vm.set_line_spacing(0.1)
        assert vm.line_spacing == ReaderViewModel.MIN_LINE_SPACING
        vm.set_line_spacing(9.9)
        assert vm.line_spacing == ReaderViewModel.MAX_LINE_SPACING

    def test_reset_typography(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        vm.set_font_size(22)
        vm.set_column_width(ColumnWidth.WIDE)
        with qtbot.waitSignal(vm.typography_changed, timeout=1000):
            vm.reset_typography()
        assert vm.font_size == ReaderViewModel.DEFAULT_FONT_SIZE
        assert vm.column_width == ColumnWidth.OPTIMAL

    def test_reset_typography_no_op_at_defaults(self, qt_app, chapter_repo) -> None:
        del qt_app
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        emitted: list[None] = []
        vm.typography_changed.connect(lambda: emitted.append(None))
        vm.reset_typography()
        assert emitted == []

    def test_pop_out_emits_chapter_id(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        added = chapter_repo.add(_ch(1))
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        vm.load_chapter(added.id)
        with qtbot.waitSignal(vm.pop_out_requested, timeout=1000) as blocker:
            vm.pop_out()
        assert blocker.args[0] == added.id

    def test_pop_out_no_chapter_is_silent(self, qt_app, chapter_repo) -> None:
        del qt_app
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        emitted: list[int] = []
        vm.pop_out_requested.connect(emitted.append)
        vm.pop_out()
        assert emitted == []
