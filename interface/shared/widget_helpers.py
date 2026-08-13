from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QLabel, QMessageBox, QScrollArea, QWidget

from interface.theme import DEFAULT_THEME_NAME, get_theme


def set_secondary_text(label: QLabel) -> None:
    """Muted/secondary text color — replaces the old QSS
    `QLabel[secondary="true"] { color: ... }` selector pattern with a
    direct QPalette set, the most common QSS-selector call site in the app
    before the zero-QSS migration."""
    palette = label.palette()
    palette.setColor(label.foregroundRole(), QColor(get_theme(DEFAULT_THEME_NAME).text_secondary))
    label.setPalette(palette)


def set_bold(label: QLabel) -> None:
    """Bold text — replaces the old QSS `font-weight: bold` rules (e.g.
    `[cardTitle="true"]`, `#commitHistoryTitle`) with a direct QFont set."""
    font = label.font()
    font.setBold(True)
    label.setFont(font)


def wrap_scrollable(widget: QWidget, *, frameless: bool = True, object_name: str | None = None) -> QScrollArea:
    """QScrollArea(widgetResizable) wrapping `widget` — the shape every
    scrollable panel/tab in this app builds by hand. `frameless` matches
    the common case (no visible border, used for tab content); pass
    False to keep QScrollArea's default frame (see conflict_dialog.py,
    which wants the border since it's inside a QDialog, not a tab)."""
    scroll = QScrollArea()
    if object_name:
        scroll.setObjectName(object_name)
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    if frameless:
        scroll.setFrameShape(QFrame.NoFrame)
    return scroll


def confirm_action(parent: QWidget, title: str, message: str) -> bool:
    """QMessageBox.warning with Yes/No (defaulting to No) — the
    confirm-before-destructive-action shape every delete/revert
    confirmation in this app uses."""
    confirm = QMessageBox.warning(parent, title, message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    return confirm == QMessageBox.Yes


def show_exclusive(visible: QWidget, *hidden: QWidget) -> None:
    """Shows `visible` and hides every widget in `hidden` — the
    empty-state/content-state (or empty/not-cloned/content) toggle every
    page's set_repo() does."""
    visible.setVisible(True)
    for widget in hidden:
        widget.setVisible(False)
