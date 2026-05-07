from __future__ import annotations

from chapter_extractor.views.theme.palettes import PaletteFactory
from chapter_extractor.views.theme.stylesheet import StylesheetBuilder
from chapter_extractor.views.theme.tokens import ThemeTokens


class TestPaletteFactory:
    def test_dark_returns_dark_tokens(self) -> None:
        t = PaletteFactory.dark()
        assert isinstance(t, ThemeTokens)
        assert t.is_dark is True
        assert t.name == "dark"

    def test_light_returns_light_tokens(self) -> None:
        t = PaletteFactory.light()
        assert t.is_dark is False
        assert t.name == "light"

    def test_dark_and_light_use_same_accent(self) -> None:
        # Indigo accent stays consistent across modes (only surfaces flip).
        assert PaletteFactory.dark().colors.accent == PaletteFactory.light().colors.accent

    def test_dark_text_not_pure_white(self) -> None:
        # Per dark-mode UX research: pure #FFFFFF on dark causes eye strain.
        primary = PaletteFactory.dark().colors.text_primary
        assert primary != "#FFFFFF"
        assert primary != "#ffffff"

    def test_dark_bg_not_pure_black(self) -> None:
        # Material 3 + Linear: deep neutral, never #000000.
        bg = PaletteFactory.dark().colors.bg_base
        assert bg.lower() != "#000000"


class TestStylesheetBuilder:
    def test_builds_non_empty(self) -> None:
        qss = StylesheetBuilder(PaletteFactory.dark()).build()
        assert len(qss) > 1000  # something substantial

    def test_uses_token_values(self) -> None:
        tokens = PaletteFactory.dark()
        qss = StylesheetBuilder(tokens).build()
        # Sanity: every QSS string should reference the accent + base colors.
        assert tokens.colors.accent in qss
        assert tokens.colors.bg_base in qss
        assert tokens.colors.text_primary in qss

    def test_light_and_dark_produce_different_qss(self) -> None:
        dark = StylesheetBuilder(PaletteFactory.dark()).build()
        light = StylesheetBuilder(PaletteFactory.light()).build()
        assert dark != light

    def test_qss_includes_role_selectors(self) -> None:
        # Views opt into themed surfaces via Qt dynamic properties — ensure
        # the stylesheet includes the matching selectors.
        qss = StylesheetBuilder(PaletteFactory.dark()).build()
        for selector in (
            'QWidget[role="sidebar"]',
            'QWidget[role="reader"]',
            'QWidget[role="titlebar"]',
            'QPushButton[primary="true"]',
            'QLabel[role="empty-state"]',
        ):
            assert selector in qss, f"missing selector: {selector}"
