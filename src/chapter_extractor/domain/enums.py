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


class ViewMode(Enum):
    """Reader view layout mode."""

    DEFAULT = auto()           # 3-pane (sidebar + list + reader)
    FOCUS = auto()             # sidebar/list collapsed; reader fills window
    DISTRACTION_FREE = auto()  # toolbar also hidden inside focus


class ColumnWidth(Enum):
    """Reader column width in characters (per typography research, 66 optimal)."""

    NARROW = 50
    OPTIMAL = 66
    WIDE = 80
