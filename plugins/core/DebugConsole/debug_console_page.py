from __future__ import annotations

import logging

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from plugin_api import QtLogHandler

_ALL_SOURCES = "All sources"


class DebugConsolePage(QWidget):
    """DebugConsole's section page — a filterable, live-updating view of
    every logging.getLogger(...) record the app has emitted, fed by
    interface_api.QtLogHandler (owned by core_api.UkoreCore, reached via
    api.debug_log_handler). Subscribes once via
    handler.log_record_emitted in __init__ and never unsubscribes: this
    page is built once in plugin.py's register(api) and lives for the
    app's whole lifetime, same as every other plugin's page_factory-
    returned instance, so there's no teardown point to unsubscribe at
    (consistent with how this app's other permanent pages don't bother
    either)."""

    def __init__(self, handler: QtLogHandler, parent=None):
        super().__init__(parent)
        self._handler = handler

        self.source_combo = QComboBox()
        self.source_combo.currentTextChanged.connect(self._refresh)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._on_clear_clicked)

        controls_row = QHBoxLayout()
        controls_row.addWidget(self.source_combo, stretch=1)
        controls_row.addWidget(self.clear_button)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
        self.log_view.setLineWrapMode(QPlainTextEdit.NoWrap)

        layout = QVBoxLayout(self)
        layout.addLayout(controls_row)
        layout.addWidget(self.log_view, stretch=1)

        self._populate_source_combo()
        self._refresh(self.source_combo.currentText())
        self._handler.log_record_emitted.connect(self._on_record)

    # -- source filter ------------------------------------------------------

    def _populate_source_combo(self) -> None:
        current = self.source_combo.currentText()
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem(_ALL_SOURCES)
        self.source_combo.addItems(self._handler.sources)
        index = self.source_combo.findText(current)
        self.source_combo.setCurrentIndex(index if index >= 0 else 0)
        self.source_combo.blockSignals(False)

    def _matches_filter(self, record: logging.LogRecord) -> bool:
        selected = self.source_combo.currentText()
        return not selected or selected == _ALL_SOURCES or record.name == selected

    # -- log content ----------------------------------------------------

    def _refresh(self, _selected_source: str) -> None:
        self._populate_source_combo()
        lines = [self._handler.format(record) for record in self._handler.records if self._matches_filter(record)]
        self.log_view.setPlainText("\n".join(lines))
        self._scroll_to_bottom()

    def _on_record(self, record: logging.LogRecord) -> None:
        if self.source_combo.findText(record.name) < 0:
            self._populate_source_combo()
        if not self._matches_filter(record):
            return
        self.log_view.appendPlainText(self._handler.format(record))
        self._scroll_to_bottom()

    def _on_clear_clicked(self) -> None:
        self._handler.clear()
        self.log_view.clear()

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
