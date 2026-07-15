from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from interface.section_registry import SectionRegistry

DEFAULT_BROWSER_LINK_ICON = Path(__file__).resolve().parent.parent.parent / "data" / "icons" / "icons8-browser-50.png"


class SectionTabList(QListWidget):
    """Vertical replacement for the old horizontal TopTabBar: one row per
    registered SectionRegistry section (built-in and plugin-provided alike,
    in registry order), then one row per dynamic Browser Link on the active
    repo (see add_dynamic_tab — inserted right after the fixed sections on
    every repo switch). Setting is deliberately NOT a row here — it's its
    own icon-only button in Sidebar's footer, next to the GitHub username,
    since it's an app-level control rather than a repo-scoped one (see
    interface/sidebar/sidebar.py)."""

    navigation_changed = Signal(str)

    def __init__(self, parent=None, *, section_registry: SectionRegistry):
        super().__init__(parent)
        self.setObjectName("sectionTabList")

        self._fixed_count = 0
        for spec in section_registry.ordered():
            self._add_row(spec.key, spec.label, spec.icon_path)
            self._fixed_count += 1

        self._dynamic_count = 0

        self.currentRowChanged.connect(self._on_current_row_changed)
        self.setCurrentRow(0)

    def _add_row(self, key: str, label: str, icon_path: Path | None, *, index: int | None = None) -> None:
        item = QListWidgetItem(label)
        item.setData(Qt.UserRole, key)
        if icon_path is not None and icon_path.exists():
            item.setIcon(QIcon(str(icon_path)))
        if index is None:
            self.addItem(item)
        else:
            self.insertItem(index, item)

    def add_dynamic_tab(self, key: str, label: str, icon_path: Path | None = None) -> None:
        """Inserted right after the fixed sections and any earlier dynamic
        tabs. icon_path defaults to the generic Browser Link icon when the
        link has no per-link override (see
        BrowserLinksSettingsPage._on_change_browser_link_icon in
        interface/settings/browser_links_settings_page.py)."""
        self._add_row(
            key, label, icon_path or DEFAULT_BROWSER_LINK_ICON, index=self._fixed_count + self._dynamic_count
        )
        self._dynamic_count += 1

    def clear_dynamic_tabs(self) -> None:
        for _ in range(self._dynamic_count):
            self.takeItem(self._fixed_count)
        self._dynamic_count = 0

    def set_visible_keys(self, visible_keys: set[str] | None) -> None:
        """Hides/shows the fixed (plugin-provided) rows for per-repo Plugin
        gating — visible_keys=None means "no restriction", every fixed row
        shown. Dynamic Browser Link rows are never affected by this."""
        for row in range(self._fixed_count):
            key = self.item(row).data(Qt.UserRole)
            hidden = visible_keys is not None and key not in visible_keys
            self.setRowHidden(row, hidden)

    def select(self, key: str) -> None:
        """Programmatically selects the row for `key` without emitting
        navigation_changed (setCurrentRow() otherwise would) — callers that
        switch tabs on the app's own behalf (e.g. "Browse" from a Submit-tab
        commit card) must also call MainWindow's own navigation handler
        themselves."""
        row = self._row_for_key(key)
        if row is None:
            return
        blocked = self.blockSignals(True)
        self.setCurrentRow(row)
        self.blockSignals(blocked)

    def _row_for_key(self, key: str) -> int | None:
        for row in range(self.count()):
            if self.item(row).data(Qt.UserRole) == key:
                return row
        return None

    def _on_current_row_changed(self, row: int) -> None:
        if row < 0:
            return
        self.navigation_changed.emit(self.item(row).data(Qt.UserRole))
