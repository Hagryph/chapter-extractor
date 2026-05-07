from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.domain.enums import ChapterStatus  # noqa: E402
from chapter_extractor.domain.models import Chapter  # noqa: E402
from chapter_extractor.viewmodels.trash_vm import TrashViewModel  # noqa: E402


def _ch(n: int) -> Chapter:
    return Chapter(
        number=n,
        title=f"T{n}",
        content="x",
        filename=f"Chapter_{n:03d}.txt",
        file_path=Path(f"Chapter_{n:03d}.txt"),
        status=ChapterStatus.EXTRACTED,
        word_count=1,
        created_at=datetime.now(),
        modified_at=datetime.now(),
    )


class TestTrashViewModel:
    def test_lists_and_restores(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        added = chapter_repo.add(_ch(1))
        chapter_repo.soft_delete(added.id)

        vm = TrashViewModel(chapter_repo)
        vm.refresh()
        assert len(vm.items) == 1

        with qtbot.waitSignal(vm.chapter_restored, timeout=1000):
            vm.restore(added.id)
        assert vm.items == []

    def test_refresh_emits_signal(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        vm = TrashViewModel(chapter_repo)
        with qtbot.waitSignal(vm.trash_changed, timeout=1000):
            vm.refresh()
