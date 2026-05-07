from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.domain.enums import ChapterStatus, ViewMode  # noqa: E402
from chapter_extractor.domain.models import Chapter  # noqa: E402
from chapter_extractor.views.reader_window import ChapterReaderWindow  # noqa: E402


class FakeClipboard:
    def __init__(self) -> None:
        self.text: str | None = None

    def copy(self, text: str) -> None:
        self.text = text


def _ch(n: int, body: str) -> Chapter:
    ch = Chapter(
        number=n,
        title=f"T{n}",
        content=body,
        filename=f"Chapter_{n:03d}.txt",
        file_path=Path(f"Chapter_{n:03d}.txt"),
        status=ChapterStatus.EXTRACTED,
        created_at=datetime.now(),
        modified_at=datetime.now(),
    )
    ch.recompute_word_count()
    return ch


class TestChapterReaderWindow:
    def test_opens_and_loads_chapter(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        added = chapter_repo.add(_ch(51, "the empress walked"))
        win = ChapterReaderWindow(added.id, chapter_repo, FakeClipboard())
        try:
            qtbot.addWidget(win)
            assert win.view_model.chapter is not None
            assert win.view_model.chapter.number == 51
            assert "51" in win.windowTitle()
        finally:
            win.close()

    def test_copy_button_uses_clipboard(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        added = chapter_repo.add(_ch(1, "the body"))
        clip = FakeClipboard()
        win = ChapterReaderWindow(added.id, chapter_repo, clip)
        try:
            qtbot.addWidget(win)
            win.view_model.copy_current_content()
            assert clip.text is not None
            assert "the body" in clip.text
        finally:
            win.close()

    def test_distraction_free_toggle(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        added = chapter_repo.add(_ch(1, "body"))
        win = ChapterReaderWindow(added.id, chapter_repo, FakeClipboard())
        try:
            qtbot.addWidget(win)
            win.view_model.set_view_mode(ViewMode.DISTRACTION_FREE)
            assert win.view_model.view_mode == ViewMode.DISTRACTION_FREE
            win.view_model.exit_to_default()
            assert win.view_model.view_mode == ViewMode.DEFAULT
        finally:
            win.close()

    def test_close_emits_chapter_id(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        added = chapter_repo.add(_ch(1, "body"))
        win = ChapterReaderWindow(added.id, chapter_repo, FakeClipboard())
        qtbot.addWidget(win)
        with qtbot.waitSignal(win.closed, timeout=1000) as blocker:
            win.close()
        assert blocker.args[0] == added.id
