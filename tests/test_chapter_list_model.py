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


class TestChapterListModelBasics:
    def test_empty_row_count_zero(self, qt_app) -> None:
        del qt_app
        m = ChapterListModel()
        assert m.rowCount() == 0

    def test_replace_all_then_row_count(self, qt_app) -> None:
        del qt_app
        m = ChapterListModel()
        m.replace_all([_summary(1, 1), _summary(2, 2), _summary(3, 3)])
        assert m.rowCount() == 3

    def test_row_count_with_valid_parent_returns_zero(self, qt_app) -> None:
        # Per Qt 6 docs: list models return 0 for non-root parents.
        del qt_app
        m = ChapterListModel([_summary(1, 1)])
        valid_parent = m.index(0, 0)
        assert m.rowCount(valid_parent) == 0


class TestChapterListModelData:
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

    def test_chapter_id_role(self, qt_app) -> None:
        del qt_app
        m = ChapterListModel([_summary(99, 1, "X")])
        assert m.data(m.index(0, 0), ChapterListRoles.CHAPTER_ID) == 99

    def test_invalid_index_returns_none(self, qt_app) -> None:
        del qt_app
        from PySide6.QtCore import QModelIndex, Qt

        m = ChapterListModel([_summary(1, 1)])
        assert m.data(QModelIndex(), Qt.ItemDataRole.DisplayRole) is None

    def test_unknown_role_returns_none(self, qt_app) -> None:
        del qt_app
        m = ChapterListModel([_summary(1, 1)])
        assert m.data(m.index(0, 0), 99999) is None

    def test_header_data_returns_chapter_label(self, qt_app) -> None:
        del qt_app
        from PySide6.QtCore import Qt

        m = ChapterListModel()
        assert (
            m.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            == "Chapter"
        )


class TestChapterListModelMutations:
    def test_append_emits_rows_inserted(self, qt_app, qtbot) -> None:
        # Per Qt docs, beginInsertRows/endInsertRows is the proper signal
        # bracket for incremental adds.
        del qt_app
        m = ChapterListModel()
        with qtbot.waitSignal(m.rowsInserted, timeout=1000):
            m.append(_summary(1, 1))
        assert m.rowCount() == 1

    def test_remove_at_emits_rows_removed(self, qt_app, qtbot) -> None:
        del qt_app
        m = ChapterListModel([_summary(1, 1), _summary(2, 2)])
        with qtbot.waitSignal(m.rowsRemoved, timeout=1000):
            removed = m.remove_at(0)
        assert removed.id == 1
        assert m.rowCount() == 1

    def test_remove_at_out_of_range_raises(self, qt_app) -> None:
        del qt_app
        m = ChapterListModel([_summary(1, 1)])
        with pytest.raises(IndexError):
            m.remove_at(99)

    def test_replace_all_emits_model_reset(self, qt_app, qtbot) -> None:
        del qt_app
        m = ChapterListModel([_summary(1, 1)])
        with qtbot.waitSignal(m.modelReset, timeout=1000):
            m.replace_all([_summary(2, 2), _summary(3, 3)])
        assert m.rowCount() == 2

    def test_update_at_emits_data_changed(self, qt_app, qtbot) -> None:
        del qt_app
        m = ChapterListModel([_summary(1, 1, "Old")])
        with qtbot.waitSignal(m.dataChanged, timeout=1000):
            m.update_at(0, _summary(1, 1, "New"))
        from PySide6.QtCore import Qt

        assert "New" in m.data(m.index(0, 0), Qt.ItemDataRole.DisplayRole)

    def test_update_at_out_of_range_raises(self, qt_app) -> None:
        del qt_app
        m = ChapterListModel([_summary(1, 1)])
        with pytest.raises(IndexError):
            m.update_at(5, _summary(1, 1))


class TestChapterListModelLookup:
    def test_find_row_by_id(self, qt_app) -> None:
        del qt_app
        m = ChapterListModel([_summary(1, 1), _summary(99, 5), _summary(3, 3)])
        assert m.find_row_by_id(99) == 1
        assert m.find_row_by_id(404) == -1

    def test_summary_at_returns_or_none(self, qt_app) -> None:
        del qt_app
        m = ChapterListModel([_summary(1, 1)])
        assert m.summary_at(0).id == 1
        assert m.summary_at(99) is None
