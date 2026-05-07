from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ShortcutCategory(Enum):
    FILE = "File"
    EDIT = "Edit"
    VIEW = "View"
    TOOLS = "Tools"
    HELP = "Help"


@dataclass(frozen=True, slots=True)
class ShortcutSpec:
    """Single source of truth for one shortcut.

    ``id`` is used by views to look up the spec; ``label`` is what users see;
    ``key_sequence`` is the primary shortcut fed to ``QKeySequence``;
    ``alt_key_sequences`` are extra equivalent shortcuts (e.g. ``Ctrl+/`` and
    ``F1`` both opening the help dialog). ``status_tip`` is the longer
    description shown in the status bar (per Qt's ``QAction.statusTip``
    convention) and the cheat-sheet help dialog.
    """

    id: str
    label: str
    category: ShortcutCategory
    key_sequence: str
    status_tip: str
    alt_key_sequences: tuple[str, ...] = ()

    @property
    def all_key_sequences(self) -> tuple[str, ...]:
        return (self.key_sequence, *self.alt_key_sequences)


class ShortcutCatalog:
    """Authoritative list of every keyboard shortcut in the app.

    UI views (menu bar, toolbar tooltips, cheat-sheet dialog) read from
    here so behaviour stays consistent. Adding a new shortcut means adding
    one row here — every consumer updates automatically.
    """

    _ENTRIES: tuple[ShortcutSpec, ...] = (
        # File
        ShortcutSpec(
            id="file.add_chapters",
            label="Add Chapters…",
            category=ShortcutCategory.FILE,
            key_sequence="Ctrl+B",
            status_tip="Open the batch input dialog to paste new chapters.",
        ),
        ShortcutSpec(
            id="file.quit",
            label="Quit",
            category=ShortcutCategory.FILE,
            key_sequence="Ctrl+Q",
            status_tip="Close the application.",
        ),
        # Edit
        ShortcutSpec(
            id="edit.copy_chapter",
            label="Copy Chapter",
            category=ShortcutCategory.EDIT,
            key_sequence="Ctrl+Shift+C",
            status_tip="Copy the current chapter's text to the clipboard.",
        ),
        # View
        ShortcutSpec(
            id="view.cycle_focus",
            label="Toggle Focus Mode",
            category=ShortcutCategory.VIEW,
            key_sequence="F11",
            status_tip="Cycle: default → focus → distraction-free → default.",
        ),
        ShortcutSpec(
            id="view.distraction_free",
            label="Distraction-Free Mode",
            category=ShortcutCategory.VIEW,
            key_sequence="Ctrl+.",
            status_tip="Hide all chrome — just the text on a clean background.",
        ),
        ShortcutSpec(
            id="view.exit_modes",
            label="Exit View Mode",
            category=ShortcutCategory.VIEW,
            key_sequence="Esc",
            status_tip="Return to the default 3-pane layout.",
        ),
        ShortcutSpec(
            id="view.pop_out",
            label="Pop Out Reader",
            category=ShortcutCategory.VIEW,
            key_sequence="Ctrl+Shift+O",
            status_tip="Open the current chapter in its own resizable window.",
        ),
        # Tools
        ShortcutSpec(
            id="tools.trash",
            label="Trash…",
            category=ShortcutCategory.TOOLS,
            key_sequence="Ctrl+Shift+T",
            status_tip="View and restore soft-deleted chapters.",
        ),
        # Help
        ShortcutSpec(
            id="help.shortcuts",
            label="Keyboard Shortcuts",
            category=ShortcutCategory.HELP,
            key_sequence="Ctrl+/",
            alt_key_sequences=("F1",),
            status_tip="Show the keyboard shortcut cheat sheet.",
        ),
    )

    @classmethod
    def all(cls) -> tuple[ShortcutSpec, ...]:
        return cls._ENTRIES

    @classmethod
    def by_id(cls, shortcut_id: str) -> ShortcutSpec:
        for entry in cls._ENTRIES:
            if entry.id == shortcut_id:
                return entry
        raise KeyError(f"Unknown shortcut id: {shortcut_id}")

    @classmethod
    def by_category(cls, category: ShortcutCategory) -> tuple[ShortcutSpec, ...]:
        return tuple(e for e in cls._ENTRIES if e.category == category)

    @classmethod
    def categories_in_order(cls) -> tuple[ShortcutCategory, ...]:
        seen: list[ShortcutCategory] = []
        for entry in cls._ENTRIES:
            if entry.category not in seen:
                seen.append(entry.category)
        return tuple(seen)
