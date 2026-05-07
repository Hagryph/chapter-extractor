from __future__ import annotations

from datetime import datetime

import pytest

pytest.importorskip("PySide6")

from chapter_extractor.domain.enums import ChapterStatus  # noqa: E402
from chapter_extractor.domain.models import ChapterSummary  # noqa: E402
from chapter_extractor.viewmodels.chapter_filter_proxy import ChapterFilterProxy  # noqa: E402
from chapter_extractor.viewmodels.chapter_list_model import ChapterListModel  # noqa: E402


def _make(id: int, number: int, title: str) -> ChapterSummary:
    return ChapterSummary(
        id=id,
        number=number,
        title=title,
        word_count=10,
        status=ChapterStatus.EXTRACTED,
        modified_at=datetime.now(),
    )


class TestChapterFilterProxy:
    def test_empty_filter_passes_all(self, qt_app) -> None:
        del qt_app
        src = ChapterListModel([_make(1, 1, "A"), _make(2, 2, "B")])
        proxy = ChapterFilterProxy()
        proxy.setSourceModel(src)
        assert proxy.rowCount() == 2

    def test_substring_in_title_case_insensitive(self, qt_app) -> None:
        del qt_app
        src = ChapterListModel(
            [
                _make(1, 51, "Ais Wallenstein"),
                _make(2, 52, "The Good Cop"),
                _make(3, 53, "Ariel 1"),
            ]
        )
        proxy = ChapterFilterProxy()
        proxy.setSourceModel(src)
        proxy.set_needle("ais")
        assert proxy.rowCount() == 1

    def test_filter_by_chapter_number(self, qt_app) -> None:
        del qt_app
        src = ChapterListModel([_make(1, 51, "X"), _make(2, 52, "Y"), _make(3, 510, "Z")])
        proxy = ChapterFilterProxy()
        proxy.setSourceModel(src)
        proxy.set_needle("51")
        # 51 matches "51" and "510" (substring)
        assert proxy.rowCount() == 2

    def test_clearing_needle_restores_all(self, qt_app) -> None:
        del qt_app
        src = ChapterListModel([_make(1, 1, "A"), _make(2, 2, "B")])
        proxy = ChapterFilterProxy()
        proxy.setSourceModel(src)
        proxy.set_needle("a")
        proxy.set_needle("")
        assert proxy.rowCount() == 2
