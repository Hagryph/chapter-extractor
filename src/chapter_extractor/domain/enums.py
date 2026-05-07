from __future__ import annotations

from enum import Enum, auto


class ChapterStatus(Enum):
    """Lifecycle of a parsed chapter relative to its persisted state."""

    NEW = auto()
    EXTRACTED = auto()
    MODIFIED = auto()
    MISSING_FILE = auto()


class EditReason(Enum):
    """Why a chapter_versions row was inserted."""

    EXTRACT = "extract"
    EDIT = "edit"
    RESTORE = "restore"
    AUTO = "auto"


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
