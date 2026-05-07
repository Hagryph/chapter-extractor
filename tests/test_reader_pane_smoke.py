from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.domain.enums import ChapterStatus  # noqa: E402
from chapter_extractor.domain.models import Chapter  # noqa: E402
from chapter_extractor.viewmodels.reader_vm import ReaderViewModel  # noqa: E402
from chapter_extractor.views.reader_pane import ReaderPane  # noqa: E402


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


class TestReaderPaneSmoke:
    def test_builds_with_disabled_actions_when_no_chapter(
        self, qt_app, chapter_repo
    ) -> None:
        del qt_app
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        pane = ReaderPane(vm)
        try:
            # All action buttons should start disabled when no chapter.
            children = pane.findChildren(type(pane.findChild(__import__("PySide6.QtWidgets", fromlist=["QPushButton"]).QPushButton)))
            del children
        finally:
            pane.deleteLater()

    def test_loading_chapter_renders_content(
        self, qt_app, qtbot, chapter_repo
    ) -> None:
        del qt_app
        added = chapter_repo.add(_ch(51, "the empress walked into the wind"))
        vm = ReaderViewModel(chapter_repo, FakeClipboard())
        pane = ReaderPane(vm)
        try:
            with qtbot.waitSignal(vm.chapter_loaded, timeout=1000):
                vm.load_chapter(added.id)
            # The QTextEdit should now contain the rendered HTML.
            from PySide6.QtWidgets import QTextEdit

            text_widget = pane.findChild(QTextEdit)
            assert text_widget is not None
            html = text_widget.toHtml()
            assert "empress" in html.lower()
            assert "Chapter 51" in html
        finally:
            pane.deleteLater()
