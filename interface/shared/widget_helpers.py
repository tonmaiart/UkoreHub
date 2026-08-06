from __future__ import annotations

from PySide6.QtWidgets import QFrame, QMessageBox, QScrollArea, QWidget


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
