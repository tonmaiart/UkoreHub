from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from core.extensibility import debug_log

_ALL_SOURCES = "All sources"


class DebugConsolePage(QWidget):
    """DebugConsole's section page — a filterable, live-updating view of
    core.extensibility.debug_log's in-memory entries. Subscribes once via
    debug_log.add_listener and never unsubscribes: this page is built once
    in plugin.py's register(api) and lives for the app's whole lifetime,
    same as every other plugin's page_factory-returned instance, so there's
    no teardown point to unsubscribe at (consistent with how this app's
    other permanent pages don't bother either)."""

    def __init__(self, parent=None):
        super().__init__(parent)

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
        debug_log.add_listener(self._on_entry)

    # -- source filter ------------------------------------------------------

    def _populate_source_combo(self) -> None:
        current = self.source_combo.currentText()
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem(_ALL_SOURCES)
        self.source_combo.addItems(debug_log.sources())
        index = self.source_combo.findText(current)
        self.source_combo.setCurrentIndex(index if index >= 0 else 0)
        self.source_combo.blockSignals(False)

    def _matches_filter(self, entry: debug_log.DebugLogEntry) -> bool:
        selected = self.source_combo.currentText()
        return not selected or selected == _ALL_SOURCES or entry.source == selected

    # -- log content ----------------------------------------------------

    def _refresh(self, _selected_source: str) -> None:
        self._populate_source_combo()
        lines = [self._format(entry) for entry in debug_log.entries() if self._matches_filter(entry)]
        self.log_view.setPlainText("\n".join(lines))
        self._scroll_to_bottom()

    def _on_entry(self, entry: debug_log.DebugLogEntry) -> None:
        if self.source_combo.findText(entry.source) < 0:
            self._populate_source_combo()
        if not self._matches_filter(entry):
            return
        self.log_view.appendPlainText(self._format(entry))
        self._scroll_to_bottom()

    def _on_clear_clicked(self) -> None:
        debug_log.clear()
        self.log_view.clear()

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @staticmethod
    def _format(entry: debug_log.DebugLogEntry) -> str:
        return f"[{entry.timestamp}] [{entry.source}] {entry.message}"
