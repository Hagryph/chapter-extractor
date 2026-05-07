from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QDialogButtonBox  # noqa: E402

from chapter_extractor.services.parser import ChapterParser  # noqa: E402
from chapter_extractor.viewmodels.batch_input_vm import BatchInputViewModel  # noqa: E402
from chapter_extractor.views.dialogs.batch_input_dialog import BatchInputDialog  # noqa: E402

BATCH = """Chapter 1: First
body of one
. . .
Chapter 2: Second
body of two
"""


class TestBatchInputDialog:
    def test_initial_state_disables_ok(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        vm = BatchInputViewModel(ChapterParser(), chapter_repo)
        dlg = BatchInputDialog(vm)
        try:
            qtbot.addWidget(dlg)
            ok_btn = dlg._buttons.button(QDialogButtonBox.StandardButton.Ok)
            assert not ok_btn.isEnabled()
        finally:
            dlg.close()

    def test_typing_enables_ok_after_debounce(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        vm = BatchInputViewModel(ChapterParser(), chapter_repo)
        dlg = BatchInputDialog(vm)
        try:
            qtbot.addWidget(dlg)
            with qtbot.waitSignal(vm.preview_changed, timeout=2000):
                dlg._editor.setPlainText(BATCH)
            ok_btn = dlg._buttons.button(QDialogButtonBox.StandardButton.Ok)
            assert ok_btn.isEnabled()
            assert "2" in dlg._summary_label.text()
        finally:
            dlg.close()

    def test_commit_persists_chapters(self, qt_app, qtbot, chapter_repo) -> None:
        del qt_app
        vm = BatchInputViewModel(ChapterParser(), chapter_repo)
        dlg = BatchInputDialog(vm)
        try:
            qtbot.addWidget(dlg)
            with qtbot.waitSignal(vm.preview_changed, timeout=2000):
                dlg._editor.setPlainText(BATCH)
            with qtbot.waitSignal(vm.commit_succeeded, timeout=2000):
                dlg._on_accept()
            assert len(chapter_repo.list_summaries()) == 2
        finally:
            dlg.close()
