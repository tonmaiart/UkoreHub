from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeColors:
    background: str
    surface: str
    surface_alt: str
    accent: str
    accent_hover: str
    text_primary: str
    text_secondary: str
    border: str
    hover: str
    error: str
    success: str
    warning: str


THEMES: dict[str, ThemeColors] = {
    "grey_dark": ThemeColors(
        background="#1e1f22",
        surface="#2b2d31",
        surface_alt="#232428",
        accent="#5865f2",
        accent_hover="#4752c4",
        text_primary="#dcddde",
        text_secondary="#96989d",
        border="#3a3c41",
        hover="#35373c",
        error="#da3d3d",
        success="#3ba55d",
        warning="#e8a33d",
    ),
}

DEFAULT_THEME_NAME = "grey_dark"


def list_theme_names() -> list[str]:
    return list(THEMES.keys())


def get_theme(name: str) -> ThemeColors:
    return THEMES.get(name, THEMES[DEFAULT_THEME_NAME])


def build_stylesheet(colors: ThemeColors) -> str:
    return f"""
    QWidget {{
        background-color: {colors.background};
        color: {colors.text_primary};
        font-size: 13px;
    }}
    QMainWindow, QDialog {{
        background-color: {colors.background};
    }}
    QLabel {{
        background: transparent;
    }}
    QLabel[secondary="true"] {{
        color: {colors.text_secondary};
    }}
    QPushButton {{
        background-color: {colors.surface};
        border: 1px solid {colors.border};
        border-radius: 4px;
        padding: 6px 12px;
    }}
    QPushButton:hover {{
        background-color: {colors.hover};
    }}
    QPushButton:pressed {{
        background-color: {colors.accent};
    }}
    QPushButton:disabled {{
        color: {colors.text_secondary};
        background-color: {colors.surface_alt};
    }}
    QWidget#sidebar {{
        background-color: {colors.surface};
        border-right: 1px solid {colors.border};
    }}
    QPushButton#activeRepoSelectButton {{
        text-align: left;
        padding: 8px 10px;
        border: none;
        border-radius: 0px;
        border-bottom: 1px solid {colors.border};
        background-color: {colors.surface};
    }}
    QPushButton#activeRepoSelectButton:hover {{
        background-color: {colors.hover};
    }}
    QListWidget#sectionTabList {{
        background-color: {colors.surface};
        border: none;
        outline: none;
        font-size: 14px;
    }}
    QListWidget#sectionTabList::item {{
        padding: 6px 12px;
        border: none;
    }}
    QListWidget#sectionTabList::item:hover {{
        background-color: {colors.hover};
    }}
    QListWidget#sectionTabList::item:selected {{
        background-color: {colors.accent};
        color: white;
        font-weight: bold;
    }}
    QWidget#sidebarFooter {{
        border-top: 1px solid {colors.border};
    }}
    QPushButton#sidebarSettingButton {{
        padding: 4px 8px;
    }}
    QFrame#requirementCard, QFrame#pluginCard {{
        background-color: {colors.surface};
        border: 1px solid {colors.border};
        border-radius: 4px;
        padding: 8px;
        margin-bottom: 4px;
    }}
    QFrame#commitCard {{
        background-color: {colors.surface};
        border: 1px solid {colors.border};
        border-radius: 3px;
        margin-bottom: 2px;
    }}
    QFrame#repoCard {{
        background-color: {colors.surface};
        border: 1px solid {colors.border};
        border-radius: 6px;
        padding: 10px 12px;
        margin-bottom: 6px;
    }}
    QFrame#repoCard:hover {{
        background-color: {colors.hover};
    }}
    QFrame#repoCard[selected="true"] {{
        border: 2px solid {colors.accent};
        background-color: {colors.hover};
    }}
    QFrame#repoCard[hasThumbnail="true"], QFrame#repoCard[hasThumbnail="true"]:hover,
    QFrame#repoCard[hasThumbnail="true"][selected="true"] {{
        /* No QSS border here — the selection ring on a thumbnail card is
           drawn by hand in _RepoCard.paintEvent instead, since a QSS
           border didn't reliably paint on top of a transparent background. */
        background: transparent;
    }}
    QLabel[status="cloned"] {{
        color: {colors.success};
    }}
    QLabel[status="error"] {{
        color: {colors.error};
    }}
    QLabel[status="not_cloned"] {{
        color: {colors.text_secondary};
    }}
    QLabel#commitHistoryTitle {{
        font-size: 15px;
        font-weight: bold;
        padding-bottom: 4px;
        border-bottom: 1px solid {colors.border};
    }}
    QScrollArea#commitHistoryScroll {{
        background-color: {colors.surface_alt};
        border: 1px solid {colors.border};
        border-radius: 4px;
    }}
    QScrollArea#commitHistoryScroll > QWidget > QWidget {{
        background-color: {colors.surface_alt};
    }}
    QLineEdit, QPlainTextEdit, QTextEdit {{
        background-color: {colors.surface_alt};
        border: 1px solid {colors.border};
        border-radius: 4px;
        padding: 4px;
        color: {colors.text_primary};
    }}
    QTreeWidget, QTableView, QListWidget, QTableWidget {{
        background-color: {colors.surface_alt};
        alternate-background-color: {colors.surface};
        border: 1px solid {colors.border};
        color: {colors.text_primary};
    }}
    QTreeWidget::item:selected, QTableView::item:selected, QListWidget::item:selected, QTableWidget::item:selected {{
        background-color: {colors.accent};
        color: white;
    }}
    QHeaderView::section {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border};
        padding: 4px;
    }}
    QStatusBar {{
        background-color: {colors.surface};
        border-top: 1px solid {colors.border};
    }}
    QScrollBar:vertical, QScrollBar:horizontal {{
        background: {colors.surface};
        border: none;
    }}
    QScrollBar::handle {{
        background: {colors.border};
        border-radius: 4px;
    }}
    QMenu {{
        background-color: {colors.surface};
        border: 1px solid {colors.border};
    }}
    QMenu::item:selected {{
        background-color: {colors.accent};
    }}
    """
