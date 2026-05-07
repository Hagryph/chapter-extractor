from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from chapter_extractor.domain.models import Project
from chapter_extractor.services.db.mappers import DateTimeCodec, ProjectMapper
from chapter_extractor.services.db.tables_project import ProjectMetaRow


class SqlAlchemyProjectRepository:
    """Manages the singleton project_meta row inside a project DB.

    Note: a Project's `chapters` list is fetched separately via the
    ChapterRepository — keeps this repo focused on settings/metadata.
    """

    def __init__(self, engine: Engine, root_path: Path) -> None:
        self._engine = engine
        self._root_path = root_path

    def create(self, project: Project) -> Project:
        with Session(self._engine) as session, session.begin():
            existing = session.get(ProjectMetaRow, 1)
            if existing is not None:
                raise RuntimeError(
                    "project_meta already initialised; use update_settings instead"
                )
            row = ProjectMetaRow(
                name=project.name,
                created_at=DateTimeCodec.encode(project.created_at) or datetime.now().isoformat(),
                font_size=project.settings.font_size,
                line_spacing=project.settings.line_spacing,
                column_width=project.settings.column_width,
                theme_mode=project.settings.theme_mode.value,
                soft_delete_retention_days=project.settings.soft_delete_retention_days,
            )
            session.add(row)
        return project

    def load(self, root_path: Path) -> Project:
        with Session(self._engine) as session:
            row = session.scalars(select(ProjectMetaRow).where(ProjectMetaRow.id == 1)).first()
            if row is None:
                raise RuntimeError("project_meta singleton row missing — DB not initialised")
            return ProjectMapper.to_domain(row, root_path)

    def update_settings(self, project: Project) -> Project:
        with Session(self._engine) as session, session.begin():
            row = session.get(ProjectMetaRow, 1)
            if row is None:
                raise RuntimeError("project_meta singleton row missing")
            row.name = project.name
            row.font_size = project.settings.font_size
            row.line_spacing = project.settings.line_spacing
            row.column_width = project.settings.column_width
            row.theme_mode = project.settings.theme_mode.value
            row.soft_delete_retention_days = project.settings.soft_delete_retention_days
        return project
