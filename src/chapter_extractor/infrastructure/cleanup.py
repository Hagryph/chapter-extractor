from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from chapter_extractor.domain.protocols import IChapterRepository


class SoftDeleteCleanupScheduler(QObject):
    """Runs `chapter_repo.purge_expired(retention)` periodically.

    Per Qt docs: keep a Python reference to QTimer or it gets GC'd. We hold
    one as instance state. Work is fast (single DELETE), so it can run on
    the GUI thread without blocking. Triggered once on `start()`, then every
    `interval_ms` (default 30 minutes).
    """

    purged = Signal(int)  # emits count of chapters hard-deleted

    DEFAULT_INTERVAL_MS = 30 * 60 * 1000  # 30 minutes

    def __init__(
        self,
        chapter_repo: IChapterRepository,
        retention_days_provider,
        interval_ms: int = DEFAULT_INTERVAL_MS,
    ) -> None:
        super().__init__()
        self._repo = chapter_repo
        self._retention = retention_days_provider  # callable -> int
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self._tick()  # one immediate pass on app open
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _tick(self) -> None:
        retention = max(int(self._retention()), 0)
        count = self._repo.purge_expired(retention)
        if count:
            self.purged.emit(count)
