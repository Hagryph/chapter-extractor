from __future__ import annotations

from chapter_extractor.views.theme.tokens import ThemeTokens


class StylesheetBuilder:
    """Renders a complete Qt stylesheet from a ThemeTokens instance.

    Visual signature (Raycast/Arc-inspired):
      - Generous 10–14px radii on every interactive surface
      - Vertical micro-gradients on buttons, inputs, list rows for depth
      - Accent-tinted hover background (5–8% mix) instead of bevels
      - 2px focus rings using accent color, no flat outlines
      - Frosted overlays on QMenu / popovers (high contrast over base)
      - Hairline borders only where separation is functional
    """

    def __init__(self, tokens: ThemeTokens) -> None:
        self._t = tokens

    def build(self) -> str:
        c = self._t.colors
        s = self._t.sizing
        f = self._t.typography

        # qlineargradient strings — used for soft elevation on hover/pressed.
        button_grad_normal = (
            f"qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {c.bg_surface_2}, stop:1 {c.bg_surface_1})"
        )
        button_grad_hover = (
            f"qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {c.bg_surface_3}, stop:1 {c.bg_surface_2})"
        )
        accent_grad = (
            f"qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {c.accent_hover}, stop:1 {c.accent})"
        )
        accent_grad_pressed = (
            f"qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {c.accent}, stop:1 {c.accent_pressed})"
        )

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

QMainWindow {{ background-color: {c.bg_base}; }}
QDialog {{ background-color: {c.bg_surface_1}; }}

QFrame {{ background-color: transparent; border: none; }}
QStackedWidget {{ background-color: {c.bg_base}; border: none; }}

/* ─── Scroll bars ───────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    margin: 6px 4px 6px 2px;
}}
QScrollBar::handle:vertical {{
    background: {c.bg_surface_3};
    min-height: 32px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{ background: {c.border_strong}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0; background: none; border: none;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 12px;
    margin: 2px 6px 4px 6px;
}}
QScrollBar::handle:horizontal {{
    background: {c.bg_surface_3};
    min-width: 32px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal:hover {{ background: {c.border_strong}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0; background: none; border: none;
}}

/* ─── Splitters ─────────────────────────────────────────────── */
QSplitter {{ background: {c.bg_base}; }}
QSplitter::handle {{ background: {c.border}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical   {{ height: 1px; }}
QSplitter::handle:hover {{ background: {c.accent}; }}

/* ─── Menus & menu bar ─────────────────────────────────────── */
QMenuBar {{
    background: {c.bg_base};
    border-bottom: 1px solid {c.border};
    padding: 6px 10px;
    spacing: 2px;
}}
QMenuBar::item {{
    background: transparent;
    padding: 6px 12px;
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
    padding: 8px 18px 8px 16px;
    border-radius: {s.radius_sm}px;
    color: {c.text_primary};
    margin: 1px 2px;
}}
QMenu::item:selected {{
    background: {c.accent};
    color: {c.accent_text};
}}
QMenu::item:disabled {{ color: {c.text_tertiary}; }}
QMenu::separator {{
    height: 1px;
    background: {c.border};
    margin: 5px 8px;
}}
QMenu::icon {{ padding-left: 8px; }}

/* ─── Buttons ───────────────────────────────────────────────── */
QPushButton {{
    background: {button_grad_normal};
    color: {c.text_primary};
    border: 1px solid {c.border_strong};
    border-radius: {s.radius_md}px;
    padding: 8px 18px;
    min-height: {s.button_height}px;
    font-size: {f.size_md}px;
    font-weight: {f.weight_medium};
}}
QPushButton:hover {{
    background: {button_grad_hover};
    border-color: {c.border_strong};
}}
QPushButton:pressed {{
    background: {c.bg_surface_1};
}}
QPushButton:focus {{
    outline: none;
    border: 2px solid {c.accent};
    padding: 7px 17px;
}}
QPushButton:disabled {{
    color: {c.text_tertiary};
    background: {c.bg_surface_1};
    border-color: {c.border};
}}

QPushButton[primary="true"] {{
    background: {accent_grad};
    color: {c.accent_text};
    border: 1px solid {c.accent_pressed};
    font-weight: {f.weight_semibold};
}}
QPushButton[primary="true"]:hover {{
    background: {accent_grad_pressed};
    border-color: {c.accent_pressed};
}}
QPushButton[primary="true"]:pressed {{
    background: {c.accent_pressed};
}}
QPushButton[primary="true"]:disabled {{
    background: {c.bg_surface_2};
    color: {c.text_tertiary};
    border-color: {c.border};
}}

QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: {s.radius_sm}px;
    padding: 6px 10px;
    color: {c.text_secondary};
    min-height: 28px;
}}
QToolButton:hover {{
    background: {c.bg_surface_2};
    color: {c.text_primary};
}}
QToolButton:pressed, QToolButton:checked {{
    background: {c.bg_surface_3};
    color: {c.text_primary};
    border-color: {c.border_strong};
}}

/* ─── Inputs ────────────────────────────────────────────────── */
QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser {{
    background: {c.bg_surface_1};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: {s.radius_md}px;
    padding: 8px 12px;
    selection-background-color: {c.accent};
    selection-color: {c.accent_text};
}}
QLineEdit {{ min-height: {s.input_height}px; }}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QTextBrowser:focus {{
    border: 2px solid {c.accent};
    padding: 7px 11px;
}}
QLineEdit:disabled {{ color: {c.text_tertiary}; }}

/* ─── Lists / trees ─────────────────────────────────────────── */
QListView, QListWidget, QTreeView, QTreeWidget {{
    background: transparent;
    color: {c.text_primary};
    border: none;
    padding: 4px;
    outline: none;
    show-decoration-selected: 1;
}}
QListView::item, QListWidget::item, QTreeView::item, QTreeWidget::item {{
    padding: 9px 12px;
    border-radius: {s.radius_sm}px;
    color: {c.text_primary};
    margin: 1px 2px;
}}
QListView::item:hover, QListWidget::item:hover,
QTreeView::item:hover, QTreeWidget::item:hover {{
    background: {c.bg_surface_2};
}}
QListView::item:selected, QListWidget::item:selected,
QTreeView::item:selected, QTreeWidget::item:selected {{
    background: {accent_grad};
    color: {c.accent_text};
    font-weight: {f.weight_medium};
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
    padding: 8px 12px;
    font-weight: {f.weight_medium};
}}

/* ─── Labels / headings ────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {c.text_primary};
}}
QLabel[role="dim"] {{ color: {c.text_secondary}; }}
QLabel[role="muted"] {{ color: {c.text_tertiary}; font-size: {f.size_sm}px; }}
QLabel[role="heading"] {{
    font-size: {f.size_lg}px;
    font-weight: {f.weight_semibold};
}}
QLabel[role="title"] {{
    color: {c.text_secondary};
    font-size: {f.size_sm}px;
    font-weight: {f.weight_semibold};
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
QLabel[role="empty-state"] {{
    color: {c.text_tertiary};
    font-size: {f.size_lg}px;
    font-weight: {f.weight_regular};
}}
QLabel[role="warning"] {{ color: {c.state_warning}; }}
QLabel[role="danger"] {{ color: {c.state_danger}; }}

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
    padding: 6px;
}}
QToolBar::separator {{
    background: {c.border};
    width: 1px;
    margin: 6px 8px;
}}

/* ─── Tabs ─────────────────────────────────────────────────── */
QTabBar::tab {{
    background: transparent;
    color: {c.text_secondary};
    padding: 8px 16px;
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
    padding: 6px 10px;
}}

/* ─── Dialog button box ─────────────────────────────────────── */
QDialogButtonBox QPushButton {{ min-width: 96px; }}

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

/* Dialog content surfaces — matches main window depth */
QWidget[role="dialog-body"] {{
    background: {c.bg_surface_1};
}}
QWidget[role="card"] {{
    background: {c.bg_surface_2};
    border: 1px solid {c.border};
    border-radius: {s.radius_lg}px;
}}
""".strip()
