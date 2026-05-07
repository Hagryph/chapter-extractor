from __future__ import annotations

from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QFrame, QTextEdit

from chapter_extractor.domain.models import Chapter
from chapter_extractor.viewmodels.reader_vm import ReaderViewModel
from chapter_extractor.views.style import ViewStyle
from chapter_extractor.views.widgets.chapter_html_renderer import ChapterHtmlRenderer


class ReaderTextView(QTextEdit):
    """Read-only QTextEdit displaying the current chapter as HTML.

    Per Qt 6 docs, QTextEdit is "optimized to handle large documents". We
    set readOnly so users can navigate and select but not edit. Content is
    rendered as HTML so we can style author-note dividers and clamp the
    reading column to the typography-research-recommended ~66 characters.
    """

    def __init__(self, vm: ReaderViewModel) -> None:
        super().__init__()
        self._vm = vm
        self._renderer = ChapterHtmlRenderer()
        self.setReadOnly(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)

        vm.chapter_loaded.connect(self._on_chapter_loaded)
        vm.typography_changed.connect(self._refresh)

        self._render_empty()

    def _on_chapter_loaded(self, chapter: Chapter | None) -> None:
        self._refresh()
        del chapter  # state lives on the VM

    def _refresh(self) -> None:
        chapter = self._vm.chapter
        if chapter is None:
            self._render_empty()
            return
        html = self._renderer.render(
            chapter,
            font_family=ViewStyle.DEFAULT_FONT_FAMILY,
            font_size_px=self._vm.font_size,
            line_height=self._vm.line_spacing,
            column_width=self._vm.column_width,
        )
        self.setHtml(html)

    def _render_empty(self) -> None:
        self.setHtml(
            self._renderer.empty_document(
                font_family=ViewStyle.DEFAULT_FONT_FAMILY,
                font_size_px=self._vm.font_size,
            )
        )
