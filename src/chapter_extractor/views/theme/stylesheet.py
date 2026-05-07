from __future__ import annotations

from chapter_extractor.views.theme.tokens import ThemeTokens


class StylesheetBuilder:
    """Renders the global Qt stylesheet from a ThemeTokens instance.

    Step 1 of the rebuild: a single dark background, nothing else. We're
    intentionally stripped down to confirm the foundation looks right
    before stacking elements back on top one at a time.
    """

    def __init__(self, tokens: ThemeTokens) -> None:
        self._t = tokens

    def build(self) -> str:
        c = self._t.colors
        f = self._t.typography
        return f"""
* {{
    font-family: {f.font_family};
    color: {c.text_primary};
}}

QWidget {{
    background-color: {c.bg_base};
    color: {c.text_primary};
}}

QMainWindow {{
    background-color: {c.bg_base};
}}

/* Surface roles used by future steps — same color as base for now so the
   empty canvas reads as a single uninterrupted dark plane. */
QWidget[role="sidebar"]      {{ background-color: {c.bg_base}; }}
QWidget[role="reader"]       {{ background-color: {c.bg_base}; }}
QWidget[role="pane"]         {{ background-color: {c.bg_base}; }}
QWidget[role="dialog-body"]  {{ background-color: {c.bg_base}; }}
QWidget[role="card"]         {{ background-color: {c.bg_base}; }}
QLabel[role="title"]         {{ color: {c.text_secondary}; }}
QLabel[role="warning"]       {{ color: {c.state_warning}; }}
QLabel[role="empty-state"]   {{ color: {c.text_tertiary}; }}
QPushButton[primary="true"]  {{ background: {c.bg_base}; color: {c.text_primary}; }}
""".strip()
