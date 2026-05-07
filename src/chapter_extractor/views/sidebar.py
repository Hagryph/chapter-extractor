from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chapter_extractor.domain.enums import ThemeMode
from chapter_extractor.domain.models import ProjectSummary
from chapter_extractor.infrastructure.app_context import AppContext
from chapter_extractor.viewmodels.project_list_vm import ProjectListViewModel
from chapter_extractor.views.style import ViewStyle


class Sidebar(QWidget):
    """Left pane: project switcher.

    A QListWidget shows known projects (most-recent first; pinned float to top).
    Buttons below: New Project, Theme toggle. Settings button reserved.
    """

    def __init__(self, vm: ProjectListViewModel, ctx: AppContext) -> None:
        super().__init__()
        # Tag for global stylesheet — gives the sidebar its own surface
        # color + right-edge divider via QSS [role="sidebar"] rule.
        self.setProperty("role", "sidebar")
        self._vm = vm
        self._ctx = ctx
        self._build_ui()
        self._wire_signals()
        self._refresh()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
            ViewStyle.PANE_PADDING,
        )
        outer.setSpacing(ViewStyle.GRID)

        # Section header — picks up QLabel[role="title"] from the stylesheet
        # so the visual hierarchy is owned by the theme, not ad-hoc fonts.
        title = QLabel("Projects")
        title.setProperty("role", "title")
        outer.addWidget(title)

        self._list = QListWidget()
        self._list.setSelectionMode(self._list.SelectionMode.SingleSelection)
        self._list.setUniformItemSizes(True)
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.itemDoubleClicked.connect(self._on_open_clicked)
        outer.addWidget(self._list, stretch=1)

        self._open_btn = QPushButton("Open")
        self._open_btn.setEnabled(False)
        self._open_btn.clicked.connect(self._on_open_clicked)
        outer.addWidget(self._open_btn)

        self._new_btn = QPushButton("+ New Project")
        # Visual emphasis — fills with accent color via QSS [primary="true"].
        self._new_btn.setProperty("primary", True)
        self._new_btn.clicked.connect(self._on_new_clicked)
        outer.addWidget(self._new_btn)

        outer.addSpacing(ViewStyle.GRID)

        self._theme_btn = QPushButton(self._theme_label())
        self._theme_btn.clicked.connect(self._on_theme_clicked)
        outer.addWidget(self._theme_btn)

    def _wire_signals(self) -> None:
        self._vm.projects_changed.connect(self._refresh)
        self._list.currentItemChanged.connect(self._on_selection_changed)

    # ─── Slots ──────────────────────────────────────────────────

    def _refresh(self) -> None:
        self._list.clear()
        for s in self._vm.projects:
            item = QListWidgetItem(self._format_summary(s))
            item.setData(Qt.ItemDataRole.UserRole, s)
            self._list.addItem(item)

    def _on_selection_changed(
        self, current: QListWidgetItem | None, previous: QListWidgetItem | None
    ) -> None:
        del previous
        self._open_btn.setEnabled(current is not None)

    def _on_open_clicked(self, *_: object) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        summary: ProjectSummary = item.data(Qt.ItemDataRole.UserRole)
        self._vm.open(summary)

    def _on_new_clicked(self) -> None:
        from chapter_extractor.views.dialogs.new_project_dialog import (
            NewProjectDialog,
        )

        dialog = NewProjectDialog(self._ctx.paths, parent=self)
        if dialog.exec() != NewProjectDialog.DialogCode.Accepted:
            return
        root = dialog.project_root
        root.mkdir(parents=True, exist_ok=True)
        self._vm.create(dialog.project_name, root)

    def _on_theme_clicked(self) -> None:
        order = [ThemeMode.AUTO, ThemeMode.LIGHT, ThemeMode.DARK]
        current = self._ctx.settings.theme_mode
        nxt = order[(order.index(current) + 1) % len(order)]
        self._ctx.settings.set_theme_mode(nxt)
        self._theme_btn.setText(self._theme_label())

    # ─── Helpers ────────────────────────────────────────────────

    def _theme_label(self) -> str:
        labels = {
            ThemeMode.AUTO: "Theme: Auto",
            ThemeMode.LIGHT: "Theme: Light",
            ThemeMode.DARK: "Theme: Dark",
        }
        return labels[self._ctx.settings.theme_mode]

    @staticmethod
    def _format_summary(s: ProjectSummary) -> str:
        prefix = "📌 " if s.pinned else ""
        return f"{prefix}{s.name}"
