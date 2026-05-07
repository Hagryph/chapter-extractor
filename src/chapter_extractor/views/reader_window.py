from __future__ import annotations

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from chapter_extractor.domain.enums import ColumnWidth, ViewMode
from chapter_extractor.domain.models import Chapter
from chapter_extractor.domain.protocols import IChapterRepository, IClipboard
from chapter_extractor.viewmodels.reader_vm import ReaderViewModel
from chapter_extractor.views.style import ViewStyle
from chapter_extractor.views.widgets.reader_text import ReaderTextView


class ChapterReaderWindow(QMainWindow):
    """Standalone pop-out reader.

    Each instance owns its own ReaderViewModel bound to the shared chapter
    repo + clipboard, so font/spacing/column tweaks here don't bleed back
    to the main reader pane. Lifetime managed by WindowManager (PR 3).
    """

    SETTINGS_GEOMETRY_KEY = "reader_window/geometry"
    closed = Signal(int)  # emits chapter_id when destroyed

    def __init__(
        self,
        chapter_id: int,
        chapter_repo: IChapterRepository,
        clipboard: IClipboard,
    ) -> None:
        super().__init__()
        self._chapter_id = chapter_id
        self._settings = QSettings("Hagryph", "ChapterExtractor")
        self._vm = ReaderViewModel(chapter_repo, clipboard, parent=self)

        self.setWindowTitle("Chapter Reader")
        self.setMinimumSize(640, 480)

        self._build_ui()
        self._build_actions()
        self._restore_geometry()

        self._vm.chapter_loaded.connect(self._on_chapter_loaded)
        self._vm.view_mode_changed.connect(self._on_view_mode_changed)
        self._vm.load_chapter(chapter_id)

    # ─── UI ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._toolbar = self._build_toolbar()
        self.addToolBar(self._toolbar)

        self._text = ReaderTextView(self._vm)
        layout.addWidget(self._text, stretch=1)

        bottom = QWidget()
        b_layout = QHBoxLayout(bottom)
        b_layout.setContentsMargins(
            ViewStyle.PANE_PADDING,
            ViewStyle.GRID,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
        )

        self._copy_btn = QPushButton("📋 Copy")
        self._copy_btn.clicked.connect(self._vm.copy_current_content)
        b_layout.addStretch()
        b_layout.addWidget(self._copy_btn)
        layout.addWidget(bottom)

        self.setCentralWidget(central)

    def _build_toolbar(self) -> QToolBar:
        tb = QToolBar("Reader")
        tb.setMovable(False)

        a_smaller = QAction("A−", self)
        a_smaller.setToolTip("Smaller text  (Ctrl+-)")
        a_smaller.setShortcut(QKeySequence("Ctrl+-"))
        a_smaller.triggered.connect(lambda: self._vm.adjust_font_size(-1))
        tb.addAction(a_smaller)

        a_larger = QAction("A+", self)
        a_larger.setToolTip("Larger text  (Ctrl++)")
        a_larger.setShortcut(QKeySequence("Ctrl++"))
        a_larger.triggered.connect(lambda: self._vm.adjust_font_size(1))
        tb.addAction(a_larger)

        a_reset = QAction("A∅", self)
        a_reset.setToolTip("Reset typography  (Ctrl+0)")
        a_reset.setShortcut(QKeySequence("Ctrl+0"))
        a_reset.triggered.connect(self._vm.reset_typography)
        tb.addAction(a_reset)

        tb.addSeparator()

        for label, w in (
            ("Narrow", ColumnWidth.NARROW),
            ("Optimal", ColumnWidth.OPTIMAL),
            ("Wide", ColumnWidth.WIDE),
        ):
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(w == ColumnWidth.OPTIMAL)
            act.triggered.connect(lambda _checked, w=w: self._vm.set_column_width(w))
            tb.addAction(act)

        return tb

    def _build_actions(self) -> None:
        # F11 cycle, Esc exit, Ctrl+. distraction-free, Ctrl+W close, Ctrl+Shift+C copy
        self._act_cycle = QAction(self)
        self._act_cycle.setShortcut(QKeySequence(Qt.Key.Key_F11))
        self._act_cycle.triggered.connect(self._vm.cycle_view_mode)
        self.addAction(self._act_cycle)

        self._act_exit = QAction(self)
        self._act_exit.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        self._act_exit.triggered.connect(self._vm.exit_to_default)
        self.addAction(self._act_exit)

        self._act_df = QAction(self)
        self._act_df.setShortcut(QKeySequence("Ctrl+."))
        self._act_df.triggered.connect(self._toggle_distraction_free)
        self.addAction(self._act_df)

        self._act_copy = QAction(self)
        self._act_copy.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self._act_copy.triggered.connect(self._vm.copy_current_content)
        self.addAction(self._act_copy)

        self._act_close = QAction(self)
        self._act_close.setShortcut(QKeySequence("Ctrl+W"))
        self._act_close.triggered.connect(self.close)
        self.addAction(self._act_close)

    def _toggle_distraction_free(self) -> None:
        if self._vm.view_mode == ViewMode.DISTRACTION_FREE:
            self._vm.exit_to_default()
        else:
            self._vm.set_view_mode(ViewMode.DISTRACTION_FREE)

    # ─── Slots ──────────────────────────────────────────────────

    def _on_chapter_loaded(self, chapter: Chapter | None) -> None:
        if chapter is None:
            self.setWindowTitle("Chapter Reader")
        else:
            self.setWindowTitle(f"Chapter {chapter.number} — {chapter.title}")

    def _on_view_mode_changed(self, mode: ViewMode) -> None:
        if mode == ViewMode.DEFAULT:
            self._toolbar.setVisible(True)
            self.showNormal()
        elif mode == ViewMode.FOCUS:
            self._toolbar.setVisible(True)
            self.showFullScreen()
        elif mode == ViewMode.DISTRACTION_FREE:
            self._toolbar.setVisible(False)
            self.showFullScreen()

    # ─── Persistence + lifecycle ───────────────────────────────

    def _restore_geometry(self) -> None:
        geom = self._settings.value(self.SETTINGS_GEOMETRY_KEY)
        if geom:
            self.restoreGeometry(geom)
        else:
            self.resize(720, 760)

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._settings.setValue(self.SETTINGS_GEOMETRY_KEY, self.saveGeometry())
        self.closed.emit(self._chapter_id)
        super().closeEvent(event)

    # ─── Test access ───────────────────────────────────────────

    @property
    def view_model(self) -> ReaderViewModel:
        return self._vm
