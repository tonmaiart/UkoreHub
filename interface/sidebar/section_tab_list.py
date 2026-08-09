from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QWidget

from interface.section_registry import SectionRegistry

DEFAULT_BROWSER_LINK_ICON = Path(__file__).resolve().parent.parent.parent / "assets" / "icons" / "icons8-browser-50.png"


class SectionTabList(QListWidget):
    """Vertical replacement for the old horizontal TopTabBar: one row per
    registered SectionRegistry section (built-in and plugin-provided alike,
    in registry order), then one row per dynamic Browser Link on the active
    repo (see add_dynamic_tab — inserted
    right after the fixed sections on every repo switch). Setting is
    deliberately NOT a row here — it's its own icon-only button in
    Sidebar's footer, next to the GitHub username, since it's an app-level
    control rather than a repo-scoped one (see interface/sidebar/sidebar.py).

    A Browser Link row is a bit different from every other row: clicking it
    opens the link in the OS's default browser (external_link_activated,
    handled in interface/main_window.py via QDesktopServices.openUrl)
    rather than switching view_stack to some page — no QtWebEngine/embedded
    browser tab involved. It never becomes the "current" row for this
    reason: clicking it snaps selection straight back to whatever was
    selected before, so the highlighted row always still reflects the
    actually-visible page.

    Every row (fixed or dynamic alike) is built the same way, as one
    composite QWidget installed via setItemWidget — not native
    QListWidgetItem icon/text — so every row looks identical whether or not
    it uses SectionSpec.trailing_widget_factory (e.g.
    plugins/core/Notification/'s unread badge). Qt still paints the
    item's own selection/hover background underneath a transparent
    itemWidget, so interface/theme.py's ::item/::item:hover/::item:selected rules
    keep working unchanged; only the *text* color/weight on selection can't
    come from ::item anymore (there's no native text to color once
    setItemWidget is used) — QLabel#sectionTabLabel[current="true"] in
    interface/theme.py covers that instead, toggled by _update_current_label."""

    navigation_changed = Signal(str)
    external_link_activated = Signal(str)

    def __init__(self, parent=None, *, section_registry: SectionRegistry):
        super().__init__(parent)
        self.setObjectName("sectionTabList")

        self._row_labels: dict[str, QLabel] = {}
        self._external_urls: dict[str, str] = {}
        self._current_row = 0

        self._fixed_count = 0
        for spec in section_registry.ordered():
            trailing_widget = spec.trailing_widget_factory() if spec.trailing_widget_factory is not None else None
            self._add_row(spec.key, spec.label, spec.icon_path, trailing_widget)
            self._fixed_count += 1

        self._dynamic_count = 0

        self.currentRowChanged.connect(self._on_current_row_changed)
        self.setCurrentRow(0)

    def _add_row(
        self,
        key: str,
        label: str,
        icon_path: Path | None,
        trailing_widget: QWidget | None = None,
        *,
        index: int | None = None,
    ) -> None:
        item = QListWidgetItem()
        item.setData(Qt.UserRole, key)

        row_widget = QWidget()
        row_widget.setObjectName("sectionTabRow")
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)
        if icon_path is not None and icon_path.exists():
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(str(icon_path)).pixmap(18, 18))
            layout.addWidget(icon_label)
        text_label = QLabel(label)
        text_label.setObjectName("sectionTabLabel")
        layout.addWidget(text_label, 1)
        if trailing_widget is not None:
            layout.addWidget(trailing_widget)

        if index is None:
            self.addItem(item)
        else:
            self.insertItem(index, item)
        self.setItemWidget(item, row_widget)
        self._row_labels[key] = text_label

    def add_dynamic_tab(self, key: str, label: str, icon_path: Path | None = None, *, url: str) -> None:
        """Inserted right after the fixed sections and any earlier dynamic
        tabs. icon_path defaults to the generic Browser Link icon when the
        link has no per-link override (see
        BrowserLinksSettingsPage._on_change_browser_link_icon in
        interface/browser_links/browser_links_settings_page.py). `url` is
        opened externally on click (see class docstring) rather than
        switching to an embedded page — every dynamic tab today is a
        Browser Link, so `url` is required."""
        self._add_row(
            key, label, icon_path or DEFAULT_BROWSER_LINK_ICON, index=self._fixed_count + self._dynamic_count
        )
        self._external_urls[key] = url
        self._dynamic_count += 1

    def clear_dynamic_tabs(self) -> None:
        for _ in range(self._dynamic_count):
            item = self.item(self._fixed_count)
            key = item.data(Qt.UserRole)
            self._row_labels.pop(key, None)
            self._external_urls.pop(key, None)
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
        themselves. Still updates the selected-row label styling directly,
        since that's normally driven by the same signal this blocks."""
        row = self._row_for_key(key)
        if row is None:
            return
        blocked = self.blockSignals(True)
        self.setCurrentRow(row)
        self.blockSignals(blocked)
        self._current_row = row
        self._update_current_label(row)

    def _row_for_key(self, key: str) -> int | None:
        for row in range(self.count()):
            if self.item(row).data(Qt.UserRole) == key:
                return row
        return None

    def _update_current_label(self, current_row: int) -> None:
        for row in range(self.count()):
            key = self.item(row).data(Qt.UserRole)
            label = self._row_labels.get(key)
            if label is None:
                continue
            is_current = row == current_row
            if label.property("current") == is_current:
                continue
            label.setProperty("current", is_current)
            label.style().unpolish(label)
            label.style().polish(label)

    def _on_current_row_changed(self, row: int) -> None:
        if row < 0:
            return
        key = self.item(row).data(Qt.UserRole)
        url = self._external_urls.get(key)
        if url is not None:
            # Not a real navigation — snap selection back to whatever page
            # was actually showing before this click, then open the link
            # externally. blockSignals so this doesn't re-enter here.
            blocked = self.blockSignals(True)
            self.setCurrentRow(self._current_row)
            self.blockSignals(blocked)
            self.external_link_activated.emit(url)
            return
        self._current_row = row
        self._update_current_label(row)
        self.navigation_changed.emit(key)
