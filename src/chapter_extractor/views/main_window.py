from __future__ import annotations

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QStackedWidget, QWidget

from chapter_extractor.domain.models import Project
from chapter_extractor.infrastructure.app_context import AppContext
from chapter_extractor.viewmodels.main_vm import MainViewModel
from chapter_extractor.views.chapter_list_pane import ChapterListPane
from chapter_extractor.views.empty_state import EmptyStateWidget
from chapter_extractor.views.reader_pane import ReaderPane
from chapter_extractor.views.sidebar import Sidebar
from chapter_extractor.views.style import ViewStyle


class MainWindow(QMainWindow):
    """Top-level application window — three-pane master-detail.

    Sidebar (256px) | Chapter list (320px) | Reader (800px+, stretch×3).

    Centre + right panes are wrapped in QStackedWidgets so we can swap
    between the project content and an EmptyState placeholder when no
    project is open.

    Persistence: window geometry, window state, and splitter sizes are
    restored from QSettings on construction and saved on closeEvent
    (canonical Qt pattern: ``saveState/restoreState``).
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
        # Reader gets the lion's share when window resizes.
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setStretchFactor(2, 3)

        self.setCentralWidget(self._splitter)

    def _wire_signals(self) -> None:
        self._vm.project_changed.connect(self._on_project_changed)

    # ─── Slots ──────────────────────────────────────────────────

    def _on_project_changed(self, project: Project | None) -> None:
        self._teardown_project_panes()
        if project is None:
            self._centre_stack.setCurrentWidget(self._centre_empty)
            self._reader_stack.setCurrentWidget(self._reader_empty)
            self.setWindowTitle("Chapter Extractor")
            return

        assert self._vm.chapter_list_vm is not None
        assert self._vm.reader_vm is not None

        self._centre_chapter_list = ChapterListPane(self._vm.chapter_list_vm)
        self._centre_stack.addWidget(self._centre_chapter_list)
        self._centre_stack.setCurrentWidget(self._centre_chapter_list)

        self._reader_pane = ReaderPane(self._vm.reader_vm)
        self._reader_stack.addWidget(self._reader_pane)
        self._reader_stack.setCurrentWidget(self._reader_pane)

        self.setWindowTitle(f"Chapter Extractor — {project.name}")

    def _teardown_project_panes(self) -> None:
        for stack, attr in (
            (self._centre_stack, "_centre_chapter_list"),
            (self._reader_stack, "_reader_pane"),
        ):
            widget = getattr(self, attr)
            if widget is not None:
                stack.removeWidget(widget)
                widget.deleteLater()
                setattr(self, attr, None)

    def request_batch_input(self) -> None:
        # Hook for ChapterListPane → batch input dialog (PR 6).
        pass

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

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._settings.setValue(ViewStyle.KEY_WINDOW_GEOMETRY, self.saveGeometry())
        self._settings.setValue(ViewStyle.KEY_WINDOW_STATE, self.saveState())
        self._settings.setValue(ViewStyle.KEY_SPLITTER_STATE, self._splitter.saveState())
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
