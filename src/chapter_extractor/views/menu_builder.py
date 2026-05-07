from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QMenu, QMenuBar

from chapter_extractor.domain.shortcuts import (
    ShortcutCatalog,
    ShortcutCategory,
    ShortcutSpec,
)


class MenuBuilder:
    """Assembles the application menu bar from the ShortcutCatalog.

    Per NN/g and Design-Bootcamp guidance, listing shortcuts next to menu
    items is the canonical passive learning channel — the menu becomes a
    cheat sheet users see whenever they click File/Edit/View.
    """

    def __init__(
        self,
        window: QMainWindow,
        handlers: dict[str, Callable[[], None]],
    ) -> None:
        self._window = window
        self._handlers = handlers
        self._actions: dict[str, QAction] = {}

    def build(self) -> QMenuBar:
        bar = self._window.menuBar()
        bar.setNativeMenuBar(False)  # keep menus inside the window on macOS too

        for category in ShortcutCatalog.categories_in_order():
            menu = bar.addMenu(self._menu_label(category))
            self._populate_menu(menu, category)

        return bar

    @property
    def actions(self) -> dict[str, QAction]:
        return self._actions

    def _populate_menu(self, menu: QMenu, category: ShortcutCategory) -> None:
        for spec in ShortcutCatalog.by_category(category):
            handler = self._handlers.get(spec.id)
            if handler is None:
                continue  # not all categories may have a handler in early PRs
            action = self._make_action(spec, handler)
            menu.addAction(action)
            self._actions[spec.id] = action

    def _make_action(self, spec: ShortcutSpec, handler: Callable[[], None]) -> QAction:
        action = QAction(spec.label, self._window)
        action.setShortcut(QKeySequence(spec.key_sequence))
        action.setStatusTip(spec.status_tip)
        action.setToolTip(f"{spec.label} ({spec.key_sequence})")
        action.triggered.connect(lambda *_: handler())
        return action

    @staticmethod
    def _menu_label(category: ShortcutCategory) -> str:
        # Add ampersands for Alt-key access on Windows (e.g. &File).
        return f"&{category.value}"
