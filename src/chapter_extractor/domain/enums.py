from __future__ import annotations

from enum import Enum, auto


class ChapterStatus(Enum):
    """Lifecycle of a parsed chapter relative to its on-disk file."""

    NEW = auto()
    EXTRACTED = auto()
    MODIFIED = auto()
    MISSING_FILE = auto()
