from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QListWidget, QVBoxLayout, QWidget

from core.theme import get_theme, list_theme_names
from interface.theme_apply import apply_theme


class ColorThemePage(QWidget):
    def __init__(self, parent=None, *, current_theme: str):
        super().__init__(parent)
        self._initial_theme = current_theme

        self.list_widget = QListWidget()
        self.list_widget.addItems(list_theme_names())

        items = self.list_widget.findItems(current_theme, Qt.MatchExactly)
        if items:
            self.list_widget.setCurrentItem(items[0])

        self.swatch_row = QHBoxLayout()
        self._build_swatches(current_theme)

        self.list_widget.currentTextChanged.connect(self._on_theme_selected)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        layout.addLayout(self.swatch_row)

    def _build_swatches(self, theme_name: str) -> None:
        while self.swatch_row.count():
            item = self.swatch_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        colors = get_theme(theme_name)
        for hex_color in (colors.background, colors.surface, colors.accent, colors.text_primary):
            swatch = QFrame()
            swatch.setFixedSize(32, 32)
            swatch.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #000;")
            self.swatch_row.addWidget(swatch)
        self.swatch_row.addStretch()

    def _on_theme_selected(self, theme_name: str) -> None:
        if not theme_name:
            return
        self._build_swatches(theme_name)
        app = QApplication.instance()
        if app:
            apply_theme(app, theme_name)

    def selected_theme_name(self) -> str:
        item = self.list_widget.currentItem()
        return item.text() if item else self._initial_theme
