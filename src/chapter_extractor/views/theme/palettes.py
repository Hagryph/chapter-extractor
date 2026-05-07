from __future__ import annotations

from chapter_extractor.views.theme.tokens import (
    ColorTokens,
    SizingTokens,
    ThemeTokens,
    TypographyTokens,
)


class PaletteFactory:
    """Constructs the two concrete ThemeTokens instances for our app.

    Visual direction: Raycast / Arc.

    Signatures of the inspiration apps:
      - Black-blue base (Raycast: ~#1A1A1A; Arc: ~#0D0D0F) — slightly cool
      - Vibrant indigo/violet accent with glow on focus (no flat outlines)
      - 12px radii — generous, not corporate
      - Soft elevation: hover surfaces lift a small step in luminance
      - Frosted overlays: menus & popovers ride on top with high contrast
    """

    # Raycast/Arc-grade indigo with two assist tones for gradient hover surfaces
    _ACCENT = "#6E56F7"        # primary brand
    _ACCENT_HOVER = "#8266FF"  # 1 step lighter for hover
    _ACCENT_PRESSED = "#5740DB"
    _ACCENT_GLOW = "rgba(110, 86, 247, 0.55)"

    @classmethod
    def dark(cls) -> ThemeTokens:
        colors = ColorTokens(
            # Black with a hint of blue (Arc-style). Surfaces step up by ~8% L.
            bg_base="#0B0C10",
            bg_surface_1="#13141A",
            bg_surface_2="#1B1D26",
            bg_surface_3="#252834",
            bg_overlay="#2A2D3A",
            text_primary="#F1F2F5",
            text_secondary="#9094A0",
            text_tertiary="#5A5E6B",
            text_inverse="#0B0C10",
            border="rgba(255, 255, 255, 0.05)",
            border_strong="rgba(255, 255, 255, 0.12)",
            accent=cls._ACCENT,
            accent_hover=cls._ACCENT_HOVER,
            accent_pressed=cls._ACCENT_PRESSED,
            accent_text="#FFFFFF",
            state_success="#34D399",
            state_warning="#F59E0B",
            state_danger="#F43F5E",
            shadow="rgba(0, 0, 0, 0.55)",
            focus_ring=cls._ACCENT_GLOW,
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
        # Light variant in the same family — warm-cool neutral, Raycast-light vibe
        colors = ColorTokens(
            bg_base="#F4F4F7",
            bg_surface_1="#FFFFFF",
            bg_surface_2="#EDEDF1",
            bg_surface_3="#E0E1E7",
            bg_overlay="#FFFFFF",
            text_primary="#0F1115",
            text_secondary="#52555F",
            text_tertiary="#9296A1",
            text_inverse="#FFFFFF",
            border="rgba(15, 17, 21, 0.07)",
            border_strong="rgba(15, 17, 21, 0.16)",
            accent=cls._ACCENT,
            accent_hover=cls._ACCENT_HOVER,
            accent_pressed=cls._ACCENT_PRESSED,
            accent_text="#FFFFFF",
            state_success="#0F9F6E",
            state_warning="#D97706",
            state_danger="#E11D48",
            shadow="rgba(15, 17, 21, 0.10)",
            focus_ring="rgba(110, 86, 247, 0.35)",
        )
        return ThemeTokens(
            name="light",
            is_dark=False,
            colors=colors,
            sizing=SizingTokens(),
            typography=TypographyTokens(),
        )
