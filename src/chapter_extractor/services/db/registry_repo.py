from __future__ import annotations

from datetime import datetime

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from chapter_extractor.domain.enums import ThemeMode
from chapter_extractor.domain.models import AppSettings, Project, ProjectSummary
from chapter_extractor.services.db.mappers import DateTimeCodec, ProjectSummaryMapper
from chapter_extractor.services.db.tables_registry import AppSettingsRow, ProjectRow


class SqlAlchemyRegistry:
    """App-wide registry: known projects + settings."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._ensure_app_settings()

    def _ensure_app_settings(self) -> None:
        with Session(self._engine) as session, session.begin():
            existing = session.get(AppSettingsRow, 1)
            if existing is None:
                session.add(AppSettingsRow())

    def register(self, project: Project) -> ProjectSummary:
        with Session(self._engine) as session, session.begin():
            root = str(project.root_path.resolve())
            existing = session.scalars(
                select(ProjectRow).where(ProjectRow.root_path == root)
            ).first()
            if existing is not None:
                existing.name = project.name
                existing.last_opened_at = datetime.now().isoformat()
                session.flush()
                return ProjectSummaryMapper.to_domain(existing)
            row = ProjectRow(
                name=project.name,
                root_path=root,
                created_at=DateTimeCodec.encode(project.created_at) or datetime.now().isoformat(),
                last_opened_at=datetime.now().isoformat(),
                pinned=0,
            )
            session.add(row)
            session.flush()
            return ProjectSummaryMapper.to_domain(row)

    def unregister(self, project_id: int) -> None:
        with Session(self._engine) as session, session.begin():
            row = session.get(ProjectRow, project_id)
            if row is None:
                raise KeyError(f"Project id {project_id} not found")
            session.delete(row)

    def list_projects(self) -> list[ProjectSummary]:
        with Session(self._engine) as session:
            rows = session.scalars(
                select(ProjectRow).order_by(
                    ProjectRow.pinned.desc(),
                    ProjectRow.last_opened_at.desc().nullslast(),
                )
            ).all()
            return [ProjectSummaryMapper.to_domain(r) for r in rows]

    def touch_last_opened(self, project_id: int) -> None:
        with Session(self._engine) as session, session.begin():
            row = session.get(ProjectRow, project_id)
            if row is None:
                raise KeyError(f"Project id {project_id} not found")
            row.last_opened_at = datetime.now().isoformat()

    def set_pinned(self, project_id: int, pinned: bool) -> None:
        with Session(self._engine) as session, session.begin():
            row = session.get(ProjectRow, project_id)
            if row is None:
                raise KeyError(f"Project id {project_id} not found")
            row.pinned = 1 if pinned else 0

    # ─── App-wide settings (singleton row) ──────────────────────────

    def get_app_settings(self) -> AppSettings:
        with Session(self._engine) as session:
            row = session.get(AppSettingsRow, 1)
            if row is None:
                raise RuntimeError("app_settings singleton row missing")
            try:
                theme = ThemeMode(row.theme_mode)
            except ValueError:
                theme = ThemeMode.AUTO
            return AppSettings(
                theme_mode=theme,
                last_project_id=row.last_project_id,
                soft_delete_retention_days=row.soft_delete_retention_days,
            )

    def update_app_settings(self, settings: AppSettings) -> AppSettings:
        with Session(self._engine) as session, session.begin():
            row = session.get(AppSettingsRow, 1)
            if row is None:
                raise RuntimeError("app_settings singleton row missing")
            row.theme_mode = settings.theme_mode.value
            row.last_project_id = settings.last_project_id
            row.soft_delete_retention_days = settings.soft_delete_retention_days
        return settings
