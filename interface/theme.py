from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeColors:
    """App-wide chrome now comes from qdarktheme (see theme_apply.py) — these
    fields are only the ones custom QPainter-drawn widgets (project_graph_view.py)
    and direct QColor/QPalette call sites still pull colors from directly,
    to stay visually consistent with qdarktheme's own dark palette."""

    surface_alt: str
    accent: str
    accent_hover: str
    text_primary: str
    text_secondary: str
    border: str


THEMES: dict[str, ThemeColors] = {
    "grey_dark": ThemeColors(
        surface_alt="#232428",
        accent="#5865f2",
        accent_hover="#4752c4",
        text_primary="#dcddde",
        text_secondary="#96989d",
        border="#3a3c41",
    ),
}

DEFAULT_THEME_NAME = "grey_dark"


def list_theme_names() -> list[str]:
    return list(THEMES.keys())


def get_theme(name: str) -> ThemeColors:
    return THEMES.get(name, THEMES[DEFAULT_THEME_NAME])
