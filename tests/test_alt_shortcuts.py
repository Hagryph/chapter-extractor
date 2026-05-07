from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMainWindow  # noqa: E402

from chapter_extractor.domain.shortcuts import ShortcutCatalog  # noqa: E402
from chapter_extractor.views.menu_builder import MenuBuilder  # noqa: E402


class TestAlternateShortcuts:
    def test_help_has_f1_alt(self) -> None:
        spec = ShortcutCatalog.by_id("help.shortcuts")
        assert "F1" in spec.alt_key_sequences
        assert spec.key_sequence == "Ctrl+/"

    def test_all_key_sequences_includes_primary_and_alts(self) -> None:
        spec = ShortcutCatalog.by_id("help.shortcuts")
        assert spec.all_key_sequences == ("Ctrl+/", "F1")

    def test_specs_without_alts_default_to_empty_tuple(self) -> None:
        spec = ShortcutCatalog.by_id("file.add_chapters")
        assert spec.alt_key_sequences == ()
        assert spec.all_key_sequences == ("Ctrl+B",)

    def test_menu_builder_registers_all_alt_keys(self, qt_app, qtbot) -> None:
        del qt_app
        win = QMainWindow()
        qtbot.addWidget(win)
        handlers = {s.id: lambda: None for s in ShortcutCatalog.all()}
        builder = MenuBuilder(win, handlers)
        builder.build()

        action = builder.actions["help.shortcuts"]
        bound = [seq.toString() for seq in action.shortcuts()]
        # Both Ctrl+/ and F1 should be active for the same QAction.
        assert any("F1" in s for s in bound)
        assert any("/" in s for s in bound)
