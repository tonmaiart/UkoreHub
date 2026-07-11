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
    QPushButton#sectionButton {{
        text-align: left;
        padding: 10px 14px;
        border: none;
        border-radius: 0;
        background-color: {colors.surface_alt};
    }}
    QPushButton#sectionButton:hover {{
        background-color: {colors.hover};
    }}
    QPushButton#sectionButton:checked {{
        background-color: {colors.accent};
        color: white;
        font-weight: bold;
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
