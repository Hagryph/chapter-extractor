from __future__ import annotations

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QSplitter, QStackedWidget, QWidget

from chapter_extractor.domain.enums import ViewMode
from chapter_extractor.domain.models import Project
from chapter_extractor.infrastructure.app_context import AppContext
from chapter_extractor.infrastructure.window_manager import WindowManager
from chapter_extractor.viewmodels.main_vm import MainViewModel
from chapter_extractor.views.chapter_list_pane import ChapterListPane
from chapter_extractor.views.dialogs.batch_input_dialog import BatchInputDialog
from chapter_extractor.views.dialogs.trash_dialog import TrashDialog
from chapter_extractor.views.empty_state import EmptyStateWidget
from chapter_extractor.views.reader_pane import ReaderPane
from chapter_extractor.views.reader_window import ChapterReaderWindow
from chapter_extractor.views.sidebar import Sidebar
from chapter_extractor.views.style import ViewStyle


class _ReaderWindowFactory:
    """Adapter so WindowManager can build ChapterReaderWindow without
    knowing about repo / clipboard plumbing."""

    def __init__(self, window: MainWindow) -> None:
        self._window = window

    def create(self, chapter_id: int):  # noqa: ANN201
        ctx = self._window._ctx
        vm = self._window._vm
        chapter_repo = vm.chapter_list_vm.source_model and vm._project  # noqa: SLF001
        del chapter_repo  # placeholder so we use the real repo via VM below
        # We reach into MainViewModel for the chapter repository it created.
        # This is a deliberately small surface: only ChapterReaderWindow is
        # ever constructed via this factory, and only while a project is open.
        repo = vm.chapter_list_vm._repo  # noqa: SLF001
        return ChapterReaderWindow(chapter_id, repo, ctx.clipboard)


class MainWindow(QMainWindow):
    """Top-level application window — three-pane master-detail with focus
    modes, pop-out windows, batch input, and trash dialogs.

    Persistence: window geometry, window state, and splitter sizes are
    restored from QSettings on construction and saved on closeEvent.
    """

    SETTINGS_ORG = "Hagryph"
    SETTINGS_APP = "ChapterExtractor"

    def __init__(self, ctx: AppContext, vm: MainViewModel) -> None:
        super().__init__()
        self._ctx = ctx
        self._vm = vm
        self._settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        self.setWindowTitle("Chapter Extractor")
        self.setMinimumSize(QSize(900, 560))

        self._build_ui()
        self._build_actions()

        # Window manager held only while a project is open. Built lazily on
        # the first project_changed (so we can pass the right repo).
        self._window_manager: WindowManager | None = None

        self._wire_signals()
        self._restore_state()

    # ─── UI build ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setChildrenCollapsible(False)

        self._sidebar = Sidebar(self._vm.project_list_vm, self._ctx)
        self._sidebar.setMinimumWidth(ViewStyle.SIDEBAR_MIN)

        self._centre_stack = QStackedWidget()
        self._centre_stack.setMinimumWidth(ViewStyle.LIST_MIN)
        self._centre_empty = EmptyStateWidget("No project open.")
        self._centre_stack.addWidget(self._centre_empty)
        self._centre_chapter_list: ChapterListPane | None = None

        self._reader_stack = QStackedWidget()
        self._reader_stack.setMinimumWidth(ViewStyle.READER_MIN)
        self._reader_empty = EmptyStateWidget("Select a project to start reading.")
        self._reader_stack.addWidget(self._reader_empty)
        self._reader_pane: ReaderPane | None = None

        self._splitter.addWidget(self._sidebar)
        self._splitter.addWidget(self._centre_stack)
        self._splitter.addWidget(self._reader_stack)
        self._splitter.setSizes(
            [
                ViewStyle.SIDEBAR_WIDTH_DEFAULT,
                ViewStyle.LIST_WIDTH_DEFAULT,
                ViewStyle.READER_WIDTH_DEFAULT,
            ]
        )
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 3)

        self.setCentralWidget(self._splitter)

    def _build_actions(self) -> None:
        # Per Qt for Python guidance, QAction is the recommended way for
        # app-wide shortcuts. Each action is a child of self (the main window)
        # so it stays alive for the window's lifetime.

        self._act_batch = QAction("Add Chapters…", self)
        self._act_batch.setShortcut(QKeySequence("Ctrl+B"))
        self._act_batch.triggered.connect(self.open_batch_input)
        self.addAction(self._act_batch)

        self._act_trash = QAction("Trash…", self)
        self._act_trash.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self._act_trash.triggered.connect(self.open_trash)
        self.addAction(self._act_trash)

        self._act_focus = QAction("Toggle Focus Mode", self)
        self._act_focus.setShortcut(QKeySequence(Qt.Key.Key_F11))
        self._act_focus.triggered.connect(self._cycle_view_mode)
        self.addAction(self._act_focus)

        self._act_distraction = QAction("Toggle Distraction-Free", self)
        self._act_distraction.setShortcut(QKeySequence("Ctrl+."))
        self._act_distraction.triggered.connect(self._toggle_distraction_free)
        self.addAction(self._act_distraction)

        self._act_exit_modes = QAction("Exit View Mode", self)
        self._act_exit_modes.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        self._act_exit_modes.triggered.connect(self._exit_view_modes)
        self.addAction(self._act_exit_modes)

        self._act_pop_out = QAction("Pop Out Reader", self)
        self._act_pop_out.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self._act_pop_out.triggered.connect(self._pop_out_current)
        self.addAction(self._act_pop_out)

        self._act_copy = QAction("Copy Chapter", self)
        self._act_copy.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self._act_copy.triggered.connect(self._copy_current)
        self.addAction(self._act_copy)

    def _wire_signals(self) -> None:
        self._vm.project_changed.connect(self._on_project_changed)

    # ─── Project lifecycle ──────────────────────────────────────

    def _on_project_changed(self, project: Project | None) -> None:
        self._teardown_project_panes()
        if project is None:
            self._centre_stack.setCurrentWidget(self._centre_empty)
            self._reader_stack.setCurrentWidget(self._reader_empty)
            self.setWindowTitle("Chapter Extractor")
            self._window_manager = None
            return

        assert self._vm.chapter_list_vm is not None
        assert self._vm.reader_vm is not None

        self._centre_chapter_list = ChapterListPane(self._vm.chapter_list_vm)
        self._centre_stack.addWidget(self._centre_chapter_list)
        self._centre_stack.setCurrentWidget(self._centre_chapter_list)

        self._reader_pane = ReaderPane(self._vm.reader_vm)
        self._reader_stack.addWidget(self._reader_pane)
        self._reader_stack.setCurrentWidget(self._reader_pane)

        # Wire pop-out: ReaderViewModel emits chapter_id; route through WM
        # so we get dedup + GC safety.
        self._window_manager = WindowManager(_ReaderWindowFactory(self))
        self._vm.reader_vm.pop_out_requested.connect(
            self._window_manager.open_for_chapter
        )
        self._vm.reader_vm.view_mode_changed.connect(self._on_view_mode_changed)

        self.setWindowTitle(f"Chapter Extractor — {project.name}")

    def _teardown_project_panes(self) -> None:
        if self._window_manager is not None:
            self._window_manager.close_all()
            self._window_manager = None
        for stack, attr in (
            (self._centre_stack, "_centre_chapter_list"),
            (self._reader_stack, "_reader_pane"),
        ):
            widget = getattr(self, attr)
            if widget is not None:
                stack.removeWidget(widget)
                widget.deleteLater()
                setattr(self, attr, None)

    # ─── Public hooks (called from panes) ───────────────────────

    def request_batch_input(self) -> None:
        self.open_batch_input()

    def open_batch_input(self) -> None:
        if self._vm.batch_input_vm is None:
            return
        dialog = BatchInputDialog(self._vm.batch_input_vm, parent=self)
        dialog.exec()

    def open_trash(self) -> None:
        if self._vm.trash_vm is None:
            return
        retention = self._vm.current_project.settings.soft_delete_retention_days if self._vm.current_project else 7
        dialog = TrashDialog(self._vm.trash_vm, retention_days=retention, parent=self)
        dialog.exec()

    # ─── View-mode handling ────────────────────────────────────

    def _cycle_view_mode(self) -> None:
        if self._vm.reader_vm is None:
            return
        self._vm.reader_vm.cycle_view_mode()

    def _toggle_distraction_free(self) -> None:
        if self._vm.reader_vm is None:
            return
        if self._vm.reader_vm.view_mode == ViewMode.DISTRACTION_FREE:
            self._vm.reader_vm.exit_to_default()
        else:
            self._vm.reader_vm.set_view_mode(ViewMode.DISTRACTION_FREE)

    def _exit_view_modes(self) -> None:
        if self._vm.reader_vm is None:
            return
        if self._vm.reader_vm.view_mode != ViewMode.DEFAULT:
            self._vm.reader_vm.exit_to_default()

    def _on_view_mode_changed(self, mode: ViewMode) -> None:
        # FOCUS hides sidebar+list; DISTRACTION_FREE additionally hides reader actions.
        if mode == ViewMode.DEFAULT:
            self._sidebar.show()
            self._centre_stack.show()
            if self._reader_pane is not None:
                self._reader_pane.set_actions_visible(True)
            self.showNormal()
        elif mode == ViewMode.FOCUS:
            self._sidebar.hide()
            self._centre_stack.hide()
            if self._reader_pane is not None:
                self._reader_pane.set_actions_visible(True)
        elif mode == ViewMode.DISTRACTION_FREE:
            self._sidebar.hide()
            self._centre_stack.hide()
            if self._reader_pane is not None:
                self._reader_pane.set_actions_visible(False)
            self.showFullScreen()

    def _pop_out_current(self) -> None:
        if self._vm.reader_vm is not None:
            self._vm.reader_vm.pop_out()

    def _copy_current(self) -> None:
        if self._vm.reader_vm is not None:
            self._vm.reader_vm.copy_current_content()

    # ─── Persistence ────────────────────────────────────────────

    def _restore_state(self) -> None:
        geom = self._settings.value(ViewStyle.KEY_WINDOW_GEOMETRY)
        if geom:
            self.restoreGeometry(geom)
        state = self._settings.value(ViewStyle.KEY_WINDOW_STATE)
        if state:
            self.restoreState(state)
        splitter_state = self._settings.value(ViewStyle.KEY_SPLITTER_STATE)
        if splitter_state:
            ok = self._splitter.restoreState(splitter_state)
            if not ok:
                self._splitter.setSizes(
                    [
                        ViewStyle.SIDEBAR_WIDTH_DEFAULT,
                        ViewStyle.LIST_WIDTH_DEFAULT,
                        ViewStyle.READER_WIDTH_DEFAULT,
                    ]
                )

    def closeEvent(self, event) -> None:  # noqa: N802
        self._settings.setValue(ViewStyle.KEY_WINDOW_GEOMETRY, self.saveGeometry())
        self._settings.setValue(ViewStyle.KEY_WINDOW_STATE, self.saveState())
        self._settings.setValue(ViewStyle.KEY_SPLITTER_STATE, self._splitter.saveState())
        if self._window_manager is not None:
            self._window_manager.close_all()
        super().closeEvent(event)

    # ─── Test access ───────────────────────────────────────────

    @property
    def splitter(self) -> QSplitter:
        return self._splitter

    @property
    def sidebar(self) -> Sidebar:
        return self._sidebar

    @property
    def centre_widget(self) -> QWidget:
        return self._centre_stack.currentWidget()

    @property
    def reader_widget(self) -> QWidget:
        return self._reader_stack.currentWidget()

    @property
    def window_manager(self) -> WindowManager | None:
        return self._window_manager
