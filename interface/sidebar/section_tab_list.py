from __future__ import annotations

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from plugin_api import SectionRegistry

_ICON_COLUMN = 0
_NAME_COLUMN = 1
_STATUS_COLUMN = 2


class SectionTabList(QObject):
    """Drives interface/MainWindow.ui's tableWidget_tab (3 columns: section
    icon, tab name, trailing status widget) — one row per registered
    SectionRegistry section, built-in and plugin-provided alike, in
    registry order. Wraps the QTableWidget the .ui already constructs
    (rather than building its own widget, unlike the old QListWidget-based
    version) since native QTableWidgetItem selection styling handles the
    current-row highlight for free — no manual font/palette bookkeeping
    needed the way setItemWidget-based QListWidget rows required. Setting
    is deliberately NOT a row here — it's its own icon-only button in
    MainWindow.ui's footer, since it's an app-level control rather than a
    repo-scoped one."""

    navigation_changed = Signal(str)

    def __init__(self, table: QTableWidget, *, section_registry: SectionRegistry, parent: QObject | None = None):
        super().__init__(parent)
        self._table = table
        self._row_for_key: dict[str, int] = {}

        table.setColumnCount(3)
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setFocusPolicy(Qt.NoFocus)
        table.horizontalHeader().setSectionResizeMode(_ICON_COLUMN, QHeaderView.Fixed)
        table.setColumnWidth(_ICON_COLUMN, 30)
        table.horizontalHeader().setSectionResizeMode(_NAME_COLUMN, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(_STATUS_COLUMN, QHeaderView.Fixed)
        table.setColumnWidth(_STATUS_COLUMN, 24)

        for spec in section_registry.ordered():
            trailing_widget = spec.trailing_widget_factory() if spec.trailing_widget_factory is not None else None
            self._add_row(spec.key, spec.label, spec.icon_path, spec.standard_icon, trailing_widget)

        table.currentCellChanged.connect(self._on_current_cell_changed)
        if table.rowCount():
            table.selectRow(0)

    def _add_row(self, key, label, icon_path, standard_icon, trailing_widget: QWidget | None) -> None:
        table = self._table
        row = table.rowCount()
        table.insertRow(row)
        self._row_for_key[key] = row

        icon_item = QTableWidgetItem()
        icon_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        icon_item.setData(Qt.UserRole, key)
        if icon_path is not None and icon_path.exists():
            icon_item.setIcon(QIcon(str(icon_path)))
        elif standard_icon is not None:
            icon_item.setIcon(table.style().standardIcon(standard_icon))
        table.setItem(row, _ICON_COLUMN, icon_item)

        name_item = QTableWidgetItem(label)
        name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        table.setItem(row, _NAME_COLUMN, name_item)

        status_item = QTableWidgetItem()
        status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        table.setItem(row, _STATUS_COLUMN, status_item)
        if trailing_widget is not None:
            table.setCellWidget(row, _STATUS_COLUMN, trailing_widget)

    def set_visible_keys(self, visible_keys: set[str] | None) -> None:
        """Hides/shows rows for per-repo Plugin gating — visible_keys=None
        means "no restriction", every row shown."""
        for key, row in self._row_for_key.items():
            hidden = visible_keys is not None and key not in visible_keys
            self._table.setRowHidden(row, hidden)

    def select(self, key: str) -> None:
        """Programmatically selects the row for `key` without emitting
        navigation_changed (selectRow() otherwise would via
        currentCellChanged) — callers that switch tabs on the app's own
        behalf (e.g. "Browse" from a Submit-tab commit card) must also call
        MainWindow's own navigation handler themselves."""
        row = self._row_for_key.get(key)
        if row is None:
            return
        blocked = self._table.blockSignals(True)
        self._table.selectRow(row)
        self._table.blockSignals(blocked)

    def _on_current_cell_changed(self, current_row: int, _current_col: int, _prev_row: int, _prev_col: int) -> None:
        if current_row < 0:
            return
        item = self._table.item(current_row, _ICON_COLUMN)
        if item is None:
            return
        self.navigation_changed.emit(item.data(Qt.UserRole))
