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
            # Step 1 of the rebuild — single near-black canvas. Tones a hair
            # warmer than pure #000 so it reads as fabric, not a void.
            # All surface levels collapse to bg_base for now; we'll separate
            # them again when we add the sidebar / reader as their own
            # element in a follow-up step.
            bg_base="#0A0A0A",
            bg_surface_1="#0A0A0A",
            bg_surface_2="#0A0A0A",
            bg_surface_3="#0A0A0A",
            bg_overlay="#111111",
            text_primary="#EDEDED",
            text_secondary="#7A7A7A",
            text_tertiary="#4A4A4A",
            text_inverse="#0A0A0A",
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
