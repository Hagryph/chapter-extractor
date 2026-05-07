from __future__ import annotations

import pytest

from chapter_extractor.domain.enums import ChapterStatus
from chapter_extractor.services.parser import ChapterParser


class TestChapterParserBasics:
    def setup_method(self) -> None:
        self.parser = ChapterParser()

    def test_returns_warning_when_no_headers(self) -> None:
        result = self.parser.parse("Just some prose with no chapter markers at all.")
        assert result.is_empty
        assert len(result.warnings) == 1
        assert "No chapter headers" in result.warnings[0].message

    def test_parses_single_chapter(self) -> None:
        text = "Chapter 7: Lonely\nThe wind blew.\n"
        result = self.parser.parse(text)
        assert len(result.chapters) == 1
        ch = result.chapters[0]
        assert ch.number == 7
        assert ch.title == "Lonely"
        assert "The wind blew." in ch.content
        assert ch.status == ChapterStatus.NEW

    def test_filename_format_zero_padded_and_slugified(self) -> None:
        text = "Chapter 51: Ais Wallenstein\nbody\n"
        result = self.parser.parse(text)
        assert result.chapters[0].filename == "Chapter_051_ais_wallenstein.txt"

    def test_word_count_populated(self) -> None:
        text = "Chapter 1: Test\none two three four five\n"
        result = self.parser.parse(text)
        assert result.chapters[0].word_count == 5


class TestChapterParserSeparators:
    def setup_method(self) -> None:
        self.parser = ChapterParser()

    def test_strips_separator_dots_between_chapters(self) -> None:
        text = (
            "Chapter 1: One\nbody one\n\n. . .\n\n"
            "Chapter 2: Two\nbody two\n\n. . .\n"
        )
        result = self.parser.parse(text)
        assert len(result.chapters) == 2
        for ch in result.chapters:
            assert ". . ." not in ch.content

    def test_collapses_excessive_blank_lines(self) -> None:
        text = "Chapter 1: T\nfirst paragraph\n\n\n\n\nsecond paragraph\n"
        result = self.parser.parse(text)
        assert "\n\n\n" not in result.chapters[0].content


class TestChapterParserEdgeCases:
    def setup_method(self) -> None:
        self.parser = ChapterParser()

    def test_handles_crlf_line_endings(self) -> None:
        text = "Chapter 1: Win\r\nWindows-style line.\r\n"
        result = self.parser.parse(text)
        assert len(result.chapters) == 1
        assert "Windows-style line." in result.chapters[0].content

    def test_handles_full_width_unicode_colon(self) -> None:
        text = "Chapter 5：Full Width\nbody\n"
        result = self.parser.parse(text)
        assert len(result.chapters) == 1
        assert result.chapters[0].title == "Full Width"

    def test_duplicate_chapter_number_emits_warning_and_keeps_last(self) -> None:
        text = "Chapter 1: First\nfirst body\n\nChapter 1: Second\nsecond body\n"
        result = self.parser.parse(text)
        assert len(result.chapters) == 1
        assert "second body" in result.chapters[0].content
        assert any("Duplicate" in w.message for w in result.warnings)

    def test_chapters_sorted_by_number(self) -> None:
        text = "Chapter 5: E\nfive\n\nChapter 2: B\ntwo\n\nChapter 9: I\nnine\n"
        result = self.parser.parse(text)
        assert [c.number for c in result.chapters] == [2, 5, 9]


class TestChapterParserAuthorNotes:
    def setup_method(self) -> None:
        self.parser = ChapterParser()

    def test_marks_inline_author_note_block(self) -> None:
        text = (
            "Chapter 58: Djinn Equip\nMain body of the chapter.\n\n"
            "(Author's Note\n\nA few thoughts on power scaling.)\n"
        )
        result = self.parser.parse(text)
        content = result.chapters[0].content
        assert "--- Author's Note ---" in content
        assert "--- End Author's Note ---" in content
        assert "A few thoughts on power scaling." in content
        assert "(Author's Note" not in content


class TestChapterParserFullBatch:
    """Golden test against a multi-chapter batch resembling real input."""

    SAMPLE = """Chapter 51: Ais Wallenstein
"And all of this is thanks to you."
The Empress transformed into the wind.

. . .

Chapter 52: The Good Cop, Bad Cop Effect
"Where is this? Where are Papa and Mama?" Ais asked in bewilderment.

. . .

Chapter 53: Ariel 1
"Yoo-hoo, I'm here. Did you miss me, darling~?" Bheara teleported into the Divine Court.

. . .
"""

    def setup_method(self) -> None:
        self.parser = ChapterParser()

    def test_parses_three_chapters(self) -> None:
        result = self.parser.parse(self.SAMPLE)
        assert [c.number for c in result.chapters] == [51, 52, 53]

    def test_titles_extracted_correctly(self) -> None:
        result = self.parser.parse(self.SAMPLE)
        titles = [c.title for c in result.chapters]
        assert titles == [
            "Ais Wallenstein",
            "The Good Cop, Bad Cop Effect",
            "Ariel 1",
        ]

    def test_no_separator_dots_in_any_content(self) -> None:
        result = self.parser.parse(self.SAMPLE)
        for ch in result.chapters:
            assert ". . ." not in ch.content

    def test_each_chapter_has_some_content(self) -> None:
        result = self.parser.parse(self.SAMPLE)
        for ch in result.chapters:
            assert ch.content.strip(), f"Chapter {ch.number} body is empty"

    def test_filenames_all_unique(self) -> None:
        result = self.parser.parse(self.SAMPLE)
        names = [c.filename for c in result.chapters]
        assert len(set(names)) == len(names)


class TestProtocolConformance:
    def test_chapter_parser_satisfies_iparser(self) -> None:
        from chapter_extractor.domain.protocols import IParser

        assert isinstance(ChapterParser(), IParser)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
