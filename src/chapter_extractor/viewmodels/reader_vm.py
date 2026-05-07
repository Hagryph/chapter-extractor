from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from chapter_extractor.domain.enums import ColumnWidth, ViewMode
from chapter_extractor.domain.models import Chapter
from chapter_extractor.domain.protocols import IChapterRepository, IClipboard


class ReaderViewModel(QObject):
    """State for the reader pane / pop-out window.

    Holds the loaded Chapter, current view mode, and typography knobs.
    Signals fire whenever any of these change so views re-render.
    """

    chapter_loaded = Signal(object)         # Chapter | None
    view_mode_changed = Signal(ViewMode)
    typography_changed = Signal()
    copy_requested = Signal(str)             # emitted after clipboard.copy
    pop_out_requested = Signal(int)          # chapter_id

    def __init__(self, repo: IChapterRepository, clipboard: IClipboard) -> None:
        super().__init__()
        self._repo = repo
        self._clipboard = clipboard
        self._chapter: Chapter | None = None
        self._view_mode = ViewMode.DEFAULT
        self._font_size = 16
        self._line_spacing = 1.6
        self._column_width = ColumnWidth.OPTIMAL

    # ─── Reads ──────────────────────────────────────────────────

    @property
    def chapter(self) -> Chapter | None:
        return self._chapter

    @property
    def view_mode(self) -> ViewMode:
        return self._view_mode

    @property
    def font_size(self) -> int:
        return self._font_size

    @property
    def line_spacing(self) -> float:
        return self._line_spacing

    @property
    def column_width(self) -> ColumnWidth:
        return self._column_width

    # ─── Commands ───────────────────────────────────────────────

    def load_chapter(self, chapter_id: int | None) -> None:
        if chapter_id is None:
            self._chapter = None
            self.chapter_loaded.emit(None)
            return
        ch = self._repo.get_by_id(chapter_id)
        self._chapter = ch
        self.chapter_loaded.emit(ch)

    def copy_current_content(self) -> None:
        if self._chapter is None:
            return
        self._clipboard.copy(self._chapter.content)
        self.copy_requested.emit(self._chapter.content)

    def pop_out(self) -> None:
        if self._chapter is None or self._chapter.id is None:
            return
        self.pop_out_requested.emit(self._chapter.id)

    def set_view_mode(self, mode: ViewMode) -> None:
        if self._view_mode == mode:
            return
        self._view_mode = mode
        self.view_mode_changed.emit(mode)

    def cycle_view_mode(self) -> None:
        order = [ViewMode.DEFAULT, ViewMode.FOCUS, ViewMode.DISTRACTION_FREE]
        i = order.index(self._view_mode)
        self.set_view_mode(order[(i + 1) % len(order)])

    def exit_to_default(self) -> None:
        self.set_view_mode(ViewMode.DEFAULT)

    def set_font_size(self, size: int) -> None:
        size = max(10, min(48, int(size)))
        if size == self._font_size:
            return
        self._font_size = size
        self.typography_changed.emit()

    def adjust_font_size(self, delta: int) -> None:
        self.set_font_size(self._font_size + delta)

    def set_line_spacing(self, spacing: float) -> None:
        spacing = max(1.0, min(2.5, float(spacing)))
        if abs(spacing - self._line_spacing) < 1e-6:
            return
        self._line_spacing = spacing
        self.typography_changed.emit()

    def set_column_width(self, width: ColumnWidth) -> None:
        if width == self._column_width:
            return
        self._column_width = width
        self.typography_changed.emit()

    def reset_typography(self) -> None:
        changed = (
            self._font_size != 16
            or abs(self._line_spacing - 1.6) > 1e-6
            or self._column_width != ColumnWidth.OPTIMAL
        )
        self._font_size = 16
        self._line_spacing = 1.6
        self._column_width = ColumnWidth.OPTIMAL
        if changed:
            self.typography_changed.emit()
