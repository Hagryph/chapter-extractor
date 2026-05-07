from __future__ import annotations

from chapter_extractor.views.theme.tokens import ThemeTokens


class StylesheetBuilder:
    """Renders a complete Qt stylesheet from a ThemeTokens instance.

    Style choices follow the modern flat-but-not-flat aesthetic:
      - Subtle elevation via small color steps, not borders+shadows
      - Hairline borders (1px) at low alpha for separation
      - 6-8px corner radii (Linear/Vercel/Raycast convention)
      - Hover states use background tint (no bevels)
      - Focus rings use accent color at low alpha
    """

    def __init__(self, tokens: ThemeTokens) -> None:
        self._t = tokens

    def build(self) -> str:
        c = self._t.colors
        s = self._t.sizing
        f = self._t.typography
        return f"""
/* ─── Base ──────────────────────────────────────────────────── */
* {{
    font-family: {f.font_family};
    color: {c.text_primary};
}}

QWidget {{
    background-color: {c.bg_base};
    color: {c.text_primary};
    font-size: {f.size_md}px;
}}

QMainWindow, QDialog {{
    background-color: {c.bg_base};
}}

QFrame {{
    background-color: transparent;
}}

/* ─── Scroll bars ───────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px 2px 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: {c.bg_surface_3};
    min-height: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{ background: {c.border_strong}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0; background: none; border: none;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 2px 4px 2px 4px;
}}
QScrollBar::handle:horizontal {{
    background: {c.bg_surface_3};
    min-width: 24px;
    border-radius: 4px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0; background: none; border: none;
}}

/* ─── Splitters ─────────────────────────────────────────────── */
QSplitter::handle {{
    background: {c.border};
}}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical   {{ height: 1px; }}
QSplitter::handle:hover {{ background: {c.accent}; }}

/* ─── Menus & menu bar ─────────────────────────────────────── */
QMenuBar {{
    background: {c.bg_base};
    border-bottom: 1px solid {c.border};
    padding: 4px 6px;
    spacing: 2px;
}}
QMenuBar::item {{
    background: transparent;
    padding: 6px 10px;
    border-radius: {s.radius_sm}px;
    color: {c.text_secondary};
}}
QMenuBar::item:selected, QMenuBar::item:hover {{
    background: {c.bg_surface_2};
    color: {c.text_primary};
}}
QMenuBar::item:pressed {{
    background: {c.bg_surface_3};
}}

QMenu {{
    background: {c.bg_overlay};
    border: 1px solid {c.border_strong};
    border-radius: {s.radius_md}px;
    padding: 6px;
}}
QMenu::item {{
    padding: 7px 16px;
    border-radius: {s.radius_sm}px;
    color: {c.text_primary};
}}
QMenu::item:selected {{
    background: {c.bg_surface_3};
    color: {c.text_primary};
}}
QMenu::separator {{
    height: 1px;
    background: {c.border};
    margin: 4px 6px;
}}

/* ─── Buttons ───────────────────────────────────────────────── */
QPushButton {{
    background: {c.bg_surface_2};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {s.radius_md}px;
    padding: 7px 14px;
    min-height: {s.button_height}px;
    font-size: {f.size_md}px;
    font-weight: {f.weight_medium};
}}
QPushButton:hover {{
    background: {c.bg_surface_3};
    border-color: {c.border_strong};
}}
QPushButton:pressed {{
    background: {c.bg_surface_1};
}}
QPushButton:focus {{
    outline: none;
    border-color: {c.accent};
}}
QPushButton:disabled {{
    color: {c.text_tertiary};
    background: {c.bg_surface_1};
    border-color: {c.border};
}}

QPushButton[primary="true"] {{
    background: {c.accent};
    color: {c.accent_text};
    border-color: {c.accent};
}}
QPushButton[primary="true"]:hover {{
    background: {c.accent_hover};
    border-color: {c.accent_hover};
}}
QPushButton[primary="true"]:pressed {{
    background: {c.accent_pressed};
    border-color: {c.accent_pressed};
}}

QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: {s.radius_sm}px;
    padding: 4px 8px;
    color: {c.text_secondary};
}}
QToolButton:hover {{
    background: {c.bg_surface_2};
    color: {c.text_primary};
}}
QToolButton:pressed, QToolButton:checked {{
    background: {c.bg_surface_3};
    color: {c.text_primary};
}}

/* ─── Inputs ────────────────────────────────────────────────── */
QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser {{
    background: {c.bg_surface_1};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {s.radius_md}px;
    padding: 6px 10px;
    selection-background-color: {c.accent};
    selection-color: {c.accent_text};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QTextBrowser:focus {{
    border-color: {c.accent};
    outline: none;
}}
QLineEdit:disabled {{ color: {c.text_tertiary}; }}

/* ─── Lists / trees / tables ────────────────────────────────── */
QListView, QListWidget, QTreeView, QTreeWidget {{
    background: {c.bg_surface_1};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {s.radius_md}px;
    padding: 4px;
    outline: none;
    show-decoration-selected: 1;
}}
QListView::item, QListWidget::item, QTreeView::item, QTreeWidget::item {{
    padding: 7px 10px;
    border-radius: {s.radius_sm}px;
    color: {c.text_primary};
}}
QListView::item:hover, QListWidget::item:hover,
QTreeView::item:hover, QTreeWidget::item:hover {{
    background: {c.bg_surface_2};
}}
QListView::item:selected, QListWidget::item:selected,
QTreeView::item:selected, QTreeWidget::item:selected {{
    background: {c.accent};
    color: {c.accent_text};
}}
QListView::item:selected:!active, QListWidget::item:selected:!active {{
    background: {c.bg_surface_3};
    color: {c.text_primary};
}}

QHeaderView::section {{
    background: {c.bg_surface_2};
    color: {c.text_secondary};
    border: none;
    border-bottom: 1px solid {c.border};
    padding: 6px 10px;
    font-weight: {f.weight_medium};
}}

/* ─── Labels / headings ────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {c.text_primary};
}}
QLabel[role="dim"] {{ color: {c.text_secondary}; }}
QLabel[role="muted"] {{ color: {c.text_tertiary}; }}
QLabel[role="heading"] {{
    font-size: {f.size_lg}px;
    font-weight: {f.weight_semibold};
}}

/* ─── Status bar ────────────────────────────────────────────── */
QStatusBar {{
    background: {c.bg_surface_1};
    border-top: 1px solid {c.border};
    color: {c.text_secondary};
    font-size: {f.size_sm}px;
}}
QStatusBar::item {{ border: none; }}

/* ─── Toolbar ──────────────────────────────────────────────── */
QToolBar {{
    background: {c.bg_surface_1};
    border-bottom: 1px solid {c.border};
    spacing: 4px;
    padding: 4px;
}}
QToolBar::separator {{
    background: {c.border};
    width: 1px;
    margin: 4px 6px;
}}

/* ─── Tabs (used in dialogs) ───────────────────────────────── */
QTabBar::tab {{
    background: transparent;
    color: {c.text_secondary};
    padding: 7px 14px;
    border: none;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:hover {{ color: {c.text_primary}; }}
QTabBar::tab:selected {{
    color: {c.text_primary};
    border-bottom-color: {c.accent};
}}

/* ─── Tooltips ─────────────────────────────────────────────── */
QToolTip {{
    background: {c.bg_overlay};
    color: {c.text_primary};
    border: 1px solid {c.border_strong};
    border-radius: {s.radius_sm}px;
    padding: 5px 9px;
}}

/* ─── App-specific role hooks ──────────────────────────────── */
QWidget[role="sidebar"] {{
    background: {c.bg_surface_1};
    border-right: 1px solid {c.border};
}}
QWidget[role="pane"] {{
    background: {c.bg_base};
}}
QWidget[role="reader"] {{
    background: {c.bg_surface_1};
    border-left: 1px solid {c.border};
}}
QWidget[role="titlebar"] {{
    background: {c.bg_base};
    border-bottom: 1px solid {c.border};
}}
QLabel[role="empty-state"] {{
    color: {c.text_tertiary};
    font-size: {f.size_lg}px;
    font-weight: {f.weight_regular};
}}
QLabel[role="title"] {{
    color: {c.text_primary};
    font-size: {f.size_md}px;
    font-weight: {f.weight_semibold};
    letter-spacing: 0.02em;
}}
""".strip()
