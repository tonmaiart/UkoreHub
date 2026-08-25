from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plugin_api import DiscoveredPlugin, UkoreHubError, confirm_action, plugin_source
from plugins.core.ExternalPluginManager.catalog_entry_dialog import CatalogEntryDialog
from plugins.core.ExternalPluginManager.catalog_store import CatalogEntry, ExternalPluginCatalog

_UI_FILE = Path(__file__).resolve().parent / "ExternalPluginManagerWindow.ui"


class ExternalPluginsPage(QWidget):
    """Settings > Project tab: backend catalog administration only — Add /
    Edit / Remove entries in this Project's own External Plugins catalog
    (Project.plugin_data["external_plugins"]["catalog"], core/models.py).
    No git status, cloning, or updating here — that moved to
    ExternalPluginUpdaterPage (external_plugin_updater_page.py), a
    top-level section rather than a Settings tab since it's the side used
    day to day. This page never touches git at all, only
    plugin_catalog (already-discovered manifests) to show each entry's own
    Requires column — the Updater page deliberately doesn't repeat it."""

    def __init__(self, parent=None, *, catalog: ExternalPluginCatalog, plugin_catalog: list[DiscoveredPlugin]):
        super().__init__(parent)
        self.catalog = catalog
        self._entries: list[CatalogEntry] = []
        self._plugin_by_id = {plugin.manifest.id: plugin for plugin in plugin_catalog}
        self._plugin_by_folder = {
            plugin.dir_path.name: plugin for plugin in plugin_catalog if plugin_source(plugin) == "repo"
        }

        # UI is authored in Qt Designer and loaded at runtime, same
        # QUiLoader pattern plugins/core/explorer/browser_widget.py uses.
        loader = QUiLoader()
        ui_file = QFile(str(_UI_FILE))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        find = self.ui.findChild
        self.table_widget: QTableWidget = find(QTableWidget, "tableWidget_external_plugin_repo")
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Name", "Requires", "Git URL", "Folder Name"])
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        add_btn: QPushButton = find(QPushButton, "pushButton_add_repo")
        edit_btn: QPushButton = find(QPushButton, "pushButton_edit_repo")
        delete_btn: QPushButton = find(QPushButton, "pushButton_remove_repo")

        add_btn.clicked.connect(self._on_add)
        edit_btn.clicked.connect(self._on_edit)
        delete_btn.clicked.connect(self._on_delete)

        self.refresh_list()

    # -- listing --------------------------------------------------------------

    def refresh_list(self) -> None:
        self._entries = self.catalog.list_entries()
        self._render()

    def _render(self) -> None:
        selected_ids = {item.data(Qt.UserRole) for item in self.table_widget.selectedItems() if item.column() == 0}
        self.table_widget.setRowCount(0)
        self.table_widget.setRowCount(len(self._entries))
        for row_index, entry in enumerate(self._entries):
            name_item = QTableWidgetItem(entry.name)
            name_item.setData(Qt.UserRole, entry.id)
            self.table_widget.setItem(row_index, 0, name_item)
            self.table_widget.setItem(row_index, 1, QTableWidgetItem(self._requires_label(entry)))
            self.table_widget.setItem(row_index, 2, QTableWidgetItem(entry.git_url))
            self.table_widget.setItem(row_index, 3, QTableWidgetItem(entry.folder_name))
            if entry.id in selected_ids:
                self.table_widget.selectRow(row_index)

    def _requires_label(self, entry: CatalogEntry) -> str:
        """'X, Y' if this entry is cloned and its manifest declares
        requirements; '' (unknown) if it isn't cloned yet — there's no
        manifest to read until then."""
        plugin = self._plugin_by_folder.get(entry.folder_name)
        if plugin is None or not plugin.manifest.requires:
            return ""
        names = [
            self._plugin_by_id[req_id].manifest.name if req_id in self._plugin_by_id else req_id
            for req_id in plugin.manifest.requires
        ]
        return ", ".join(names)

    def _selected_entry(self) -> CatalogEntry | None:
        row_index = self.table_widget.currentRow()
        if row_index < 0 or row_index >= len(self._entries):
            return None
        return self._entries[row_index]

    # -- catalog CRUD -----------------------------------------------------------

    def _on_add(self) -> None:
        dialog = CatalogEntryDialog(self)
        if dialog.exec():
            try:
                self.catalog.add_entry(dialog.name(), dialog.git_url(), dialog.folder_name())
            except UkoreHubError as exc:
                QMessageBox.warning(self, "Add External Plugin", str(exc))
                return
            self.refresh_list()

    def _on_edit(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            QMessageBox.information(self, "Edit", "Select exactly one entry first.")
            return
        dialog = CatalogEntryDialog(self, name=entry.name, git_url=entry.git_url, folder_name=entry.folder_name)
        if not dialog.exec():
            return
        try:
            self.catalog.edit_entry(
                entry.id, name=dialog.name(), git_url=dialog.git_url(), folder_name=dialog.folder_name()
            )
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Edit External Plugin", str(exc))
            return
        self.refresh_list()

    def _on_delete(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            QMessageBox.information(self, "Delete", "Select exactly one entry first.")
            return
        confirmed = confirm_action(
            self,
            "Delete External Plugin",
            f"Remove '{entry.name}' from this project's External Plugins catalog?\n\n"
            "This only removes the catalog entry — any already-cloned folder on disk is left untouched.",
        )
        if confirmed:
            self.catalog.delete_entry(entry.id)
            self.refresh_list()
