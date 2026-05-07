from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ColorTokens:
    """Semantic color tokens (no raw values referenced from QSS — only these).

    Naming follows the modern dark-system convention:
      - bg_*       : window/canvas levels (4 elevations)
      - text_*     : foreground text by hierarchy
      - border_*   : hairline borders
      - accent_*   : single-accent tint and its hover/pressed variants
      - state_*    : success / warning / danger
      - shadow     : drop shadow under floating surfaces
    """

    # Surface elevations — base = darkest, overlay = floating dropdowns/menus
    bg_base: str
    bg_surface_1: str
    bg_surface_2: str
    bg_surface_3: str
    bg_overlay: str

    # Text
    text_primary: str
    text_secondary: str
    text_tertiary: str
    text_inverse: str

    # Borders / dividers
    border: str
    border_strong: str

    # Accent (jewel-tone violet by default; pre-computed hover/pressed)
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_text: str  # text on accent backgrounds

    # State colors (used sparingly: warnings, errors, success badges)
    state_success: str
    state_warning: str
    state_danger: str

    # Effects
    shadow: str
    focus_ring: str  # accent w/ alpha for outlines


@dataclass(frozen=True, slots=True)
class SizingTokens:
    """Dimensional tokens — all multiples of an 8px grid.

    Raycast/Arc lean on generous radii (12px standard) and a slightly
    taller hit-area for inputs/buttons (36–40px) so the UI breathes.
    """

    grid: int = 8
    radius_sm: int = 6
    radius_md: int = 10
    radius_lg: int = 14
    radius_xl: int = 18
    border_width: int = 1
    pane_padding: int = 24
    titlebar_height: int = 36
    button_height: int = 36
    input_height: int = 40


@dataclass(frozen=True, slots=True)
class TypographyTokens:
    """Font stack + weights. Sizes stay in CSS px; QSS converts to pt as needed."""

    font_family: str = "'Inter', 'Segoe UI', -apple-system, system-ui, sans-serif"
    font_family_mono: str = "'JetBrains Mono', 'Cascadia Mono', Consolas, monospace"

    size_xs: int = 11
    size_sm: int = 12
    size_md: int = 13
    size_lg: int = 15
    size_xl: int = 18

    weight_regular: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600


@dataclass(frozen=True, slots=True)
class ThemeTokens:
    """Full token bundle — passed to StylesheetBuilder."""

    name: str
    is_dark: bool
    colors: ColorTokens
    sizing: SizingTokens
    typography: TypographyTokens
