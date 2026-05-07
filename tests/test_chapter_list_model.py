from __future__ import annotations

from datetime import datetime

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.domain.enums import ChapterStatus  # noqa: E402
from chapter_extractor.domain.models import ChapterSummary  # noqa: E402
from chapter_extractor.viewmodels.chapter_list_model import (  # noqa: E402
    ChapterListModel,
    ChapterListRoles,
)


def _summary(id: int, number: int, title: str = "T") -> ChapterSummary:
    return ChapterSummary(
        id=id,
        number=number,
        title=title,
        word_count=10,
        status=ChapterStatus.EXTRACTED,
        modified_at=datetime.now(),
    )


class TestChapterListModel:
    def test_empty_row_count_zero(self, qt_app) -> None:
        del qt_app
        m = ChapterListModel()
        assert m.rowCount() == 0

    def test_replace_all_then_row_count(self, qt_app) -> None:
        del qt_app
        m = ChapterListModel()
        m.replace_all([_summary(1, 1), _summary(2, 2), _summary(3, 3)])
        assert m.rowCount() == 3

    def test_display_role_format(self, qt_app) -> None:
        del qt_app
        from PySide6.QtCore import Qt

        m = ChapterListModel([_summary(1, 51, "Ais Wallenstein")])
        text = m.data(m.index(0, 0), Qt.ItemDataRole.DisplayRole)
        assert "51" in text
        assert "Ais Wallenstein" in text

    def test_summary_role_returns_object(self, qt_app) -> None:
        del qt_app
        s = _summary(7, 7, "X")
        m = ChapterListModel([s])
        assert m.data(m.index(0, 0), ChapterListRoles.SUMMARY) is s

    def test_append_emits_rows_inserted(self, qt_app, qtbot) -> None:
        del qt_app
        m = ChapterListModel()
        with qtbot.waitSignal(m.rowsInserted, timeout=1000):
            m.append(_summary(1, 1))
        assert m.rowCount() == 1

    def test_remove_at(self, qt_app, qtbot) -> None:
        del qt_app
        m = ChapterListModel([_summary(1, 1), _summary(2, 2)])
        with qtbot.waitSignal(m.rowsRemoved, timeout=1000):
            removed = m.remove_at(0)
        assert removed.id == 1
        assert m.rowCount() == 1

    def test_find_row_by_id(self, qt_app) -> None:
        del qt_app
        m = ChapterListModel([_summary(1, 1), _summary(99, 5), _summary(3, 3)])
        assert m.find_row_by_id(99) == 1
        assert m.find_row_by_id(404) == -1

    def test_invalid_index_returns_none(self, qt_app) -> None:
        del qt_app
        from PySide6.QtCore import QModelIndex, Qt

        m = ChapterListModel([_summary(1, 1)])
        assert m.data(QModelIndex(), Qt.ItemDataRole.DisplayRole) is None
