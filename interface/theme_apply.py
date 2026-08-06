from __future__ import annotations

from PySide6.QtWidgets import QApplication

from core.theme import build_stylesheet, get_theme


def apply_theme(app: QApplication, theme_name: str) -> None:
    colors = get_theme(theme_name)
    app.setStyleSheet(build_stylesheet(colors))
