from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.domain.shortcuts import ShortcutCatalog  # noqa: E402
from chapter_extractor.views.dialogs.shortcuts_dialog import ShortcutsDialog  # noqa: E402


class TestShortcutsDialog:
    def test_builds_with_every_spec(self, qt_app, qtbot) -> None:
        del qt_app
        dlg = ShortcutsDialog()
        try:
            qtbot.addWidget(dlg)
            # Tree should have one row per spec PLUS one header per category.
            spec_count = len(ShortcutCatalog.all())
            cat_count = len(ShortcutCatalog.categories_in_order())
            assert dlg._tree.topLevelItemCount() == spec_count + cat_count
        finally:
            dlg.close()

    def test_search_filters_rows(self, qt_app, qtbot) -> None:
        del qt_app
        dlg = ShortcutsDialog()
        try:
            qtbot.addWidget(dlg)
            dlg._search.setText("focus")
            visible_rows = [
                i
                for i in range(dlg._tree.topLevelItemCount())
                if not dlg._tree.topLevelItem(i).isHidden()
                and not dlg._tree.topLevelItem(i).isFirstColumnSpanned()
            ]
            # "focus" matches "Toggle Focus Mode" — exactly one shortcut row.
            assert len(visible_rows) == 1
        finally:
            dlg.close()

    def test_clearing_search_restores_all(self, qt_app, qtbot) -> None:
        del qt_app
        dlg = ShortcutsDialog()
        try:
            qtbot.addWidget(dlg)
            dlg._search.setText("focus")
            dlg._search.setText("")
            visible = sum(
                1
                for i in range(dlg._tree.topLevelItemCount())
                if not dlg._tree.topLevelItem(i).isHidden()
            )
            assert visible == dlg._tree.topLevelItemCount()
        finally:
            dlg.close()
