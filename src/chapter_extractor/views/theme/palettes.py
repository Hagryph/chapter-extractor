from __future__ import annotations

from chapter_extractor.views.theme.tokens import (
    ColorTokens,
    SizingTokens,
    ThemeTokens,
    TypographyTokens,
)


class PaletteFactory:
    """Constructs the two concrete ThemeTokens instances for our app.

    Values informed by:
      - Material 3 dark system (#121212 base, never pure black)
      - Linear / Arc / Raycast aesthetics (off-white text on dark, ~6-8px radii)
      - Baymard typography research (66ch reading column already enforced
        in views/widgets/chapter_html_renderer.py)
      - Muz.li dark-mode systems guide on 4-elevation surfaces
    """

    # Indigo / violet jewel tone (calm, premium, doesn't fight reading content)
    _ACCENT = "#7C5CFF"
    _ACCENT_HOVER = "#8E72FF"
    _ACCENT_PRESSED = "#6849E6"

    @classmethod
    def dark(cls) -> ThemeTokens:
        colors = ColorTokens(
            bg_base="#0F0F11",
            bg_surface_1="#16161A",
            bg_surface_2="#1E1E24",
            bg_surface_3="#26262E",
            bg_overlay="#2D2D36",
            text_primary="#ECECF1",
            text_secondary="#9B9BA5",
            text_tertiary="#62626C",
            text_inverse="#0F0F11",
            border="rgba(255, 255, 255, 0.06)",
            border_strong="rgba(255, 255, 255, 0.12)",
            accent=cls._ACCENT,
            accent_hover=cls._ACCENT_HOVER,
            accent_pressed=cls._ACCENT_PRESSED,
            accent_text="#FFFFFF",
            state_success="#34D399",
            state_warning="#FBBF24",
            state_danger="#F87171",
            shadow="rgba(0, 0, 0, 0.45)",
            focus_ring="rgba(124, 92, 255, 0.45)",
        )
        return ThemeTokens(
            name="dark",
            is_dark=True,
            colors=colors,
            sizing=SizingTokens(),
            typography=TypographyTokens(),
        )

    @classmethod
    def light(cls) -> ThemeTokens:
        colors = ColorTokens(
            bg_base="#FAFAFB",
            bg_surface_1="#FFFFFF",
            bg_surface_2="#F2F3F5",
            bg_surface_3="#E8E9EC",
            bg_overlay="#FFFFFF",
            text_primary="#16161A",
            text_secondary="#52525B",
            text_tertiary="#A1A1AA",
            text_inverse="#FFFFFF",
            border="rgba(0, 0, 0, 0.08)",
            border_strong="rgba(0, 0, 0, 0.16)",
            accent=cls._ACCENT,
            accent_hover=cls._ACCENT_HOVER,
            accent_pressed=cls._ACCENT_PRESSED,
            accent_text="#FFFFFF",
            state_success="#10B981",
            state_warning="#D97706",
            state_danger="#DC2626",
            shadow="rgba(15, 15, 17, 0.10)",
            focus_ring="rgba(124, 92, 255, 0.35)",
        )
        return ThemeTokens(
            name="light",
            is_dark=False,
            colors=colors,
            sizing=SizingTokens(),
            typography=TypographyTokens(),
        )
