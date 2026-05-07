from __future__ import annotations


class ViewStyle:
    """Shared visual constants. All sizes follow an 8px grid (Material/Apple HIG)
    so spacing stays consistent across panes."""

    GRID = 8

    # Pane widths (initial). Sidebar 240-280 is the documented sweet spot;
    # 256 = 16rem at 16px/rem (the Material default).
    SIDEBAR_WIDTH_DEFAULT = 256
    LIST_WIDTH_DEFAULT = 320
    READER_WIDTH_DEFAULT = 800

    SIDEBAR_MIN = 200
    LIST_MIN = 240
    READER_MIN = 480

    # Internal padding inside each pane.
    PANE_PADDING = 24
    READER_INNER_PADDING = 32

    # Typography defaults (mirrored in ReaderViewModel).
    DEFAULT_FONT_FAMILY = "Segoe UI, Inter, -apple-system, sans-serif"
    DEFAULT_FONT_SIZE_PX = 16
    DEFAULT_LINE_HEIGHT = 1.6
    OPTIMAL_COLUMN_CHARS = 66

    # QSettings keys (centralised so persistence stays consistent).
    KEY_WINDOW_GEOMETRY = "main_window/geometry"
    KEY_WINDOW_STATE = "main_window/state"
    KEY_SPLITTER_STATE = "main_window/splitter"
