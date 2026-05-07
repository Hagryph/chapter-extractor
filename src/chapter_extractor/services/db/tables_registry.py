from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from chapter_extractor.services.db.orm_base import RegistryBase


class ProjectRow(RegistryBase):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    root_path: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    last_opened_at: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    pinned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AppSettingsRow(RegistryBase):
    __tablename__ = "app_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_app_settings_singleton"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False, default=1)
    theme_mode: Mapped[str] = mapped_column(String, nullable=False, default="auto")
    last_project_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    soft_delete_retention_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=7
    )


Index("idx_projects_last_opened", ProjectRow.last_opened_at.desc())


REGISTRY_RAW_DDL = """
CREATE VIEW IF NOT EXISTS v_recent_projects AS
SELECT id, name, root_path, created_at, last_opened_at, pinned
  FROM projects
 ORDER BY pinned DESC, last_opened_at IS NULL, last_opened_at DESC;
"""


__all__ = ["ProjectRow", "AppSettingsRow", "REGISTRY_RAW_DDL"]
