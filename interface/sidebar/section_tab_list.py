from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QStyle, QWidget

from plugin_api import SectionRegistry


class SectionTabList(QListWidget):
    """Vertical replacement for the old horizontal TopTabBar: one row per
    registered SectionRegistry section (built-in and plugin-provided alike,
    in registry order). Setting is
    deliberately NOT a row here — it's its own icon-only button in
    Sidebar's footer, next to the GitHub username, since it's an app-level
    control rather than a repo-scoped one (see interface/sidebar/sidebar.py).

    Every row is built the same way, as one
    composite QWidget installed via setItemWidget — not native
    QListWidgetItem icon/text — so every row looks identical whether or not
    it uses SectionSpec.trailing_widget_factory (e.g.
    plugins/core/submit/'s status_dot QLabel). Qt still paints the item's own
    selection/hover background underneath a transparent itemWidget, using
    qdarktheme's default QListWidget item styling now that there's no
    app-specific QSS; only the *text* color/weight on selection can't come
    from the native item anymore (there's no native text to color once
    setItemWidget is used) — _update_current_label sets that directly via
    QPalette/QFont on the row's own QLabel instead."""

    navigation_changed = Signal(str)

    def __init__(self, parent=None, *, section_registry: SectionRegistry):
        super().__init__(parent)
        self.setObjectName("sectionTabList")

        self._row_labels: dict[str, QLabel] = {}
        self._normal_label_color: QColor | None = None
        self._current_row = 0

        self._fixed_count = 0
        for spec in section_registry.ordered():
            trailing_widget = spec.trailing_widget_factory() if spec.trailing_widget_factory is not None else None
            self._add_row(spec.key, spec.label, spec.icon_path, spec.standard_icon, trailing_widget)
            self._fixed_count += 1

        self.currentRowChanged.connect(self._on_current_row_changed)
        self.setCurrentRow(0)

    def _add_row(
        self,
        key: str,
        label: str,
        icon_path: Path | None,
        standard_icon: QStyle.StandardPixmap | None,
        trailing_widget: QWidget | None = None,
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
        elif standard_icon is not None:
            icon_label = QLabel()
            icon_label.setPixmap(self.style().standardIcon(standard_icon).pixmap(18, 18))
            layout.addWidget(icon_label)
        text_label = QLabel(label)
        text_label.setObjectName("sectionTabLabel")
        if self._normal_label_color is None:
            self._normal_label_color = text_label.palette().color(text_label.foregroundRole())
        layout.addWidget(text_label, 1)
        if trailing_widget is not None:
            layout.addWidget(trailing_widget)

        self.addItem(item)
        self.setItemWidget(item, row_widget)
        self._row_labels[key] = text_label

    def set_visible_keys(self, visible_keys: set[str] | None) -> None:
        """Hides/shows the fixed (plugin-provided) rows for per-repo Plugin
        gating — visible_keys=None means "no restriction", every fixed row
        shown."""
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
            font = label.font()
            font.setBold(is_current)
            label.setFont(font)
            palette = label.palette()
            palette.setColor(label.foregroundRole(), QColor(Qt.white) if is_current else self._normal_label_color)
            label.setPalette(palette)

    def _on_current_row_changed(self, row: int) -> None:
        if row < 0:
            return
        key = self.item(row).data(Qt.UserRole)
        self._current_row = row
        self._update_current_label(row)
        self.navigation_changed.emit(key)
