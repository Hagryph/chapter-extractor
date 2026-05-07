from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QMainWindow  # noqa: E402

from chapter_extractor.domain.shortcuts import ShortcutCatalog  # noqa: E402
from chapter_extractor.views.menu_builder import MenuBuilder  # noqa: E402


class TestMenuBuilder:
    def test_builds_one_menu_per_category(self, qt_app, qtbot) -> None:
        del qt_app
        win = QMainWindow()
        qtbot.addWidget(win)

        called: list[str] = []
        handlers = {s.id: lambda sid=s.id: called.append(sid) for s in ShortcutCatalog.all()}
        builder = MenuBuilder(win, handlers)
        bar = builder.build()

        # Top-level menus: one per category.
        assert len(bar.actions()) == len(ShortcutCatalog.categories_in_order())

    def test_actions_have_status_tips(self, qt_app, qtbot) -> None:
        del qt_app
        win = QMainWindow()
        qtbot.addWidget(win)

        handlers = {s.id: lambda: None for s in ShortcutCatalog.all()}
        builder = MenuBuilder(win, handlers)
        builder.build()

        for spec in ShortcutCatalog.all():
            action = builder.actions[spec.id]
            assert action.statusTip() == spec.status_tip
            assert action.shortcut().toString() != ""

    def test_action_triggered_calls_handler(self, qt_app, qtbot) -> None:
        del qt_app
        win = QMainWindow()
        qtbot.addWidget(win)

        called: list[str] = []
        handlers = {
            s.id: (lambda sid=s.id: called.append(sid)) for s in ShortcutCatalog.all()
        }
        builder = MenuBuilder(win, handlers)
        builder.build()

        target = ShortcutCatalog.by_id("view.cycle_focus")
        builder.actions[target.id].trigger()
        assert called == ["view.cycle_focus"]

    def test_missing_handler_skips_action(self, qt_app, qtbot) -> None:
        del qt_app
        win = QMainWindow()
        qtbot.addWidget(win)

        # Only register a single handler — others should be silently skipped.
        handlers = {"view.cycle_focus": lambda: None}
        builder = MenuBuilder(win, handlers)
        builder.build()
        assert "view.cycle_focus" in builder.actions
        assert "tools.trash" not in builder.actions
