from __future__ import annotations

import pytest

from chapter_extractor.services.slugify import Slugifier


class TestSlugifier:
    def setup_method(self) -> None:
        self.slug = Slugifier()

    def test_basic_lowercase_underscore(self) -> None:
        assert self.slug.slugify("Ais Wallenstein") == "ais_wallenstein"

    def test_strips_punctuation(self) -> None:
        assert self.slug.slugify("The Good Cop, Bad Cop Effect") == "the_good_cop_bad_cop_effect"

    def test_collapses_multiple_separators(self) -> None:
        assert self.slug.slugify("Ariel  ---  1") == "ariel_1"

    def test_strips_unicode_to_ascii(self) -> None:
        assert self.slug.slugify("Café résumé") == "cafe_resume"

    def test_truncates_to_max_length(self) -> None:
        slug = Slugifier(max_length=10)
        assert slug.slugify("A very long chapter title that exceeds the limit") == "a_very_lon"

    def test_empty_input_returns_untitled(self) -> None:
        assert self.slug.slugify("") == "untitled"

    def test_punctuation_only_returns_untitled(self) -> None:
        assert self.slug.slugify("!!! ??? ...") == "untitled"

    def test_strips_trailing_underscores_after_truncate(self) -> None:
        slug = Slugifier(max_length=8)
        assert slug.slugify("hello world test") == "hello_wo"

    def test_invalid_max_length_raises(self) -> None:
        with pytest.raises(ValueError):
            Slugifier(max_length=0)
