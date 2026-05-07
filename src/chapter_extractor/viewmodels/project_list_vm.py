from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from chapter_extractor.domain.models import Project, ProjectSettings, ProjectSummary
from chapter_extractor.domain.protocols import IRegistry


class ProjectListViewModel(QObject):
    """Sidebar's recent-projects list + commands."""

    projects_changed = Signal()
    project_opened = Signal(object)   # Project
    project_created = Signal(object)  # Project

    def __init__(self, registry: IRegistry) -> None:
        super().__init__()
        self._registry = registry
        self._projects: list[ProjectSummary] = []
        self.refresh()

    # ─── Reads ──────────────────────────────────────────────────

    @property
    def projects(self) -> list[ProjectSummary]:
        return list(self._projects)

    def project_at(self, row: int) -> ProjectSummary | None:
        if 0 <= row < len(self._projects):
            return self._projects[row]
        return None

    # ─── Commands ───────────────────────────────────────────────

    def refresh(self) -> None:
        self._projects = self._registry.list_projects()
        self.projects_changed.emit()

    def create(self, name: str, root_path: Path) -> Project:
        project = Project(
            name=name,
            root_path=root_path,
            settings=ProjectSettings(),
        )
        self._registry.register(project)
        self.refresh()
        self.project_created.emit(project)
        return project

    def open(self, summary: ProjectSummary) -> None:
        self._registry.touch_last_opened(summary.id)
        self.refresh()
        self.project_opened.emit(
            Project(name=summary.name, root_path=summary.root_path, created_at=summary.created_at)
        )

    def delete(self, summary: ProjectSummary) -> None:
        self._registry.unregister(summary.id)
        self.refresh()

    def toggle_pin(self, summary: ProjectSummary) -> None:
        self._registry.set_pinned(summary.id, not summary.pinned)
        self.refresh()
