from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.domain.enums import ChapterStatus  # noqa: E402
from chapter_extractor.domain.models import Chapter  # noqa: E402
from chapter_extractor.viewmodels.trash_vm import TrashViewModel  # noqa: E402
from chapter_extractor.views.dialogs.trash_dialog import TrashDialog  # noqa: E402


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


class TestTrashDialog:
    def test_lists_soft_deleted(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        added = chapter_repo.add(_ch(1))
        chapter_repo.soft_delete(added.id)

        vm = TrashViewModel(chapter_repo)
        dlg = TrashDialog(vm, retention_days=7)
        try:
            qtbot.addWidget(dlg)
            assert dlg._list.count() == 1
        finally:
            dlg.close()

    def test_restore_button_initially_disabled(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        added = chapter_repo.add(_ch(1))
        chapter_repo.soft_delete(added.id)
        vm = TrashViewModel(chapter_repo)
        dlg = TrashDialog(vm, retention_days=7)
        try:
            qtbot.addWidget(dlg)
            assert not dlg._restore_btn.isEnabled()
        finally:
            dlg.close()
