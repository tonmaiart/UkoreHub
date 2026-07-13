from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QListWidget, QStackedWidget, QWidget

from interface.settings_tab_registry import SettingsTabRegistry, SettingsTabSpec


class SettingsView(QWidget):
    """Embedded (not modal) settings UI — a permanent second view inside
    MainWindow's view_stack, switched to via ViewSwitcher. Every settings
    page persists its own changes immediately, so there's no Save/Cancel
    here."""

    def __init__(self, parent=None, *, settings_tab_registry: SettingsTabRegistry):
        super().__init__(parent)

        self.tab_list = QListWidget()
        self.tab_list.setFixedWidth(180)

        self.stack = QStackedWidget()
        self._specs: list[SettingsTabSpec] = settings_tab_registry.ordered()
        self._tab_widgets: dict[str, QWidget] = {}
        for spec in self._specs:
            widget = spec.page_factory()
            self._tab_widgets[spec.key] = widget
            self.tab_list.addItem(spec.label)
            self.stack.addWidget(widget)

        self.tab_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.tab_list.currentRowChanged.connect(self._on_tab_changed)
        self.tab_list.setCurrentRow(0)

        layout = QHBoxLayout(self)
        layout.addWidget(self.tab_list)
        layout.addWidget(self.stack, stretch=1)

    def _on_tab_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._specs):
            return
        spec = self._specs[row]
        if spec.on_activated is not None:
            spec.on_activated(self._tab_widgets[spec.key])

    def refresh_current_tab(self) -> None:
        """Re-runs the current sub-tab's on_activated — call this whenever
        the Setting view itself is switched back into, since switching
        between Repo/Setting doesn't change tab_list's row (no
        currentRowChanged to piggyback on)."""
        self._on_tab_changed(self.tab_list.currentRow())
