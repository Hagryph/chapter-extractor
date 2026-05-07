from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtWidgets import QSplitter, QStackedWidget, QWidget
from qframelesswindow import FramelessMainWindow

from chapter_extractor.domain.enums import ViewMode
from chapter_extractor.domain.models import Project
from chapter_extractor.infrastructure.app_context import AppContext
from chapter_extractor.infrastructure.window_manager import WindowManager
from chapter_extractor.viewmodels.main_vm import MainViewModel
from chapter_extractor.views.chapter_list_pane import ChapterListPane
from chapter_extractor.views.dialogs.batch_input_dialog import BatchInputDialog
from chapter_extractor.views.dialogs.shortcuts_dialog import ShortcutsDialog
from chapter_extractor.views.dialogs.trash_dialog import TrashDialog
from chapter_extractor.views.empty_state import EmptyStateWidget
from chapter_extractor.views.menu_builder import MenuBuilder
from chapter_extractor.views.reader_pane import ReaderPane
from chapter_extractor.views.reader_window import ChapterReaderWindow
from chapter_extractor.views.sidebar import Sidebar
from chapter_extractor.views.style import ViewStyle
from chapter_extractor.views.widgets.app_titlebar import AppTitleBar


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


class MainWindow(FramelessMainWindow):
    """Top-level application window — three-pane master-detail with focus
    modes, pop-out windows, batch input, and trash dialogs.

    Frameless via ``qframelesswindow.FramelessMainWindow`` so we ship a
    custom titlebar (AppTitleBar) alongside the menu bar. Native window
    behaviours (drag, resize, snap layout on Win11, double-click maximize)
    stay intact via the library's win32 hooks.

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

        # Custom titlebar — must be set before _build_ui so the menu bar
        # lands beneath it.
        repo_root = Path(__file__).resolve().parents[3]
        icon_path = repo_root / "assets" / "app.ico"
        self._titlebar = AppTitleBar(self, str(icon_path) if icon_path.exists() else None)
        self._titlebar.set_title("Chapter Extractor")
        self.setTitleBar(self._titlebar)

        self._build_ui()
        self._build_menu_and_actions()
        self._build_status_bar()

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
        self._centre_stack.setProperty("role", "pane")
        self._centre_stack.setMinimumWidth(ViewStyle.LIST_MIN)
        self._centre_empty = EmptyStateWidget("No project open.")
        self._centre_stack.addWidget(self._centre_empty)
        self._centre_chapter_list: ChapterListPane | None = None

        self._reader_stack = QStackedWidget()
        self._reader_stack.setProperty("role", "reader")
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

    def _build_menu_and_actions(self) -> None:
        # Single source of truth for shortcut→handler wiring. MenuBuilder
        # reads ShortcutCatalog and assembles File / Edit / View / Tools / Help
        # menus with proper QActions (per Qt-for-Python guidance: QAction is
        # the recommended way for app-wide shortcuts).
        handlers = {
            "file.add_chapters": self.open_batch_input,
            "file.quit": self.close,
            "edit.copy_chapter": self._copy_current,
            "view.cycle_focus": self._cycle_view_mode,
            "view.distraction_free": self._toggle_distraction_free,
            "view.exit_modes": self._exit_view_modes,
            "view.pop_out": self._pop_out_current,
            "tools.trash": self.open_trash,
            "help.shortcuts": self.open_shortcuts_dialog,
        }
        self._menu_builder = MenuBuilder(self, handlers)
        self._menu_builder.build()

    def _build_status_bar(self) -> None:
        # statusBar() lazily creates a QStatusBar. Qt automatically routes
        # QAction.statusTip() text here on hover — gives users a passive
        # description of every shortcut as they explore the menus.
        self.statusBar().showMessage("Ready")

    def _wire_signals(self) -> None:
        self._vm.project_changed.connect(self._on_project_changed)

    # ─── Project lifecycle ──────────────────────────────────────

    def _on_project_changed(self, project: Project | None) -> None:
        self._teardown_project_panes()
        if project is None:
            self._centre_stack.setCurrentWidget(self._centre_empty)
            self._reader_stack.setCurrentWidget(self._reader_empty)
            self.setWindowTitle("Chapter Extractor")
            self._titlebar.set_title("Chapter Extractor")
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

        title = f"Chapter Extractor — {project.name}"
        self.setWindowTitle(title)
        self._titlebar.set_title(title)

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
            self.statusBar().showMessage("Open a project before adding chapters.", 3000)
            return
        dialog = BatchInputDialog(self._vm.batch_input_vm, parent=self)
        dialog.exec()

    def open_trash(self) -> None:
        if self._vm.trash_vm is None:
            self.statusBar().showMessage("Open a project before viewing trash.", 3000)
            return
        retention = self._vm.current_project.settings.soft_delete_retention_days if self._vm.current_project else 7
        dialog = TrashDialog(self._vm.trash_vm, retention_days=retention, parent=self)
        dialog.exec()

    def open_shortcuts_dialog(self) -> None:
        ShortcutsDialog(parent=self).exec()

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
