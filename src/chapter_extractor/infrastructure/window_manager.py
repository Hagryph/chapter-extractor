from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMainWindow


class IReaderWindowFactory(Protocol):
    def create(self, chapter_id: int) -> QMainWindow: ...


class WindowManager(QObject):
    """Tracks pop-out reader windows.

    Two responsibilities:
      1. Hold strong references so Qt doesn't GC the spawned QMainWindows.
      2. Deduplicate: opening a chapter that already has a window raises and
         focuses it instead of spawning a duplicate.
    """

    window_opened = Signal(int)
    window_closed = Signal(int)

    def __init__(self, factory: IReaderWindowFactory) -> None:
        super().__init__()
        self._factory = factory
        self._windows: dict[int, QMainWindow] = {}

    def open_for_chapter(self, chapter_id: int) -> QMainWindow:
        existing = self._windows.get(chapter_id)
        if existing is not None:
            existing.raise_()
            existing.activateWindow()
            return existing

        window = self._factory.create(chapter_id)
        self._windows[chapter_id] = window
        window.destroyed.connect(lambda _=None, cid=chapter_id: self._on_destroyed(cid))
        window.show()
        self.window_opened.emit(chapter_id)
        return window

    def is_open(self, chapter_id: int) -> bool:
        return chapter_id in self._windows

    def close_all(self) -> None:
        for w in list(self._windows.values()):
            w.close()

    def _on_destroyed(self, chapter_id: int) -> None:
        self._windows.pop(chapter_id, None)
        self.window_closed.emit(chapter_id)
