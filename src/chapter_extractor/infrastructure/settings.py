from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from chapter_extractor.domain.enums import ThemeMode
from chapter_extractor.domain.models import AppSettings
from chapter_extractor.domain.protocols import IRegistry


class SettingsStore(QObject):
    """Observable wrapper around the registry's app_settings singleton.

    Caches the row in-process so reads are free; emits Qt signals when
    relevant fields change so listeners (e.g. ThemeManager) can react.
    """

    theme_changed = Signal(ThemeMode)
    retention_changed = Signal(int)
    last_project_changed = Signal(object)  # int | None

    def __init__(self, registry: IRegistry) -> None:
        super().__init__()
        self._registry = registry
        self._cached: AppSettings = registry.get_app_settings()

    # ─── Reads ──────────────────────────────────────────────────

    @property
    def current(self) -> AppSettings:
        return self._cached

    @property
    def theme_mode(self) -> ThemeMode:
        return self._cached.theme_mode

    @property
    def retention_days(self) -> int:
        return self._cached.soft_delete_retention_days

    @property
    def last_project_id(self) -> int | None:
        return self._cached.last_project_id

    # ─── Writes ─────────────────────────────────────────────────

    def set_theme_mode(self, mode: ThemeMode) -> None:
        if self._cached.theme_mode == mode:
            return
        self._cached.theme_mode = mode
        self._registry.update_app_settings(self._cached)
        self.theme_changed.emit(mode)

    def set_retention_days(self, days: int) -> None:
        if days < 0:
            raise ValueError("retention_days must be >= 0")
        if self._cached.soft_delete_retention_days == days:
            return
        self._cached.soft_delete_retention_days = days
        self._registry.update_app_settings(self._cached)
        self.retention_changed.emit(days)

    def set_last_project_id(self, project_id: int | None) -> None:
        if self._cached.last_project_id == project_id:
            return
        self._cached.last_project_id = project_id
        self._registry.update_app_settings(self._cached)
        self.last_project_changed.emit(project_id)

    def reload(self) -> None:
        """Re-read from DB. Useful if another component bypassed the store."""
        self._cached = self._registry.get_app_settings()
