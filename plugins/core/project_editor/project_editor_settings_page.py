from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QIcon
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QGroupBox,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plugin_api import (
    ConflictError,
    DiscoveredPlugin,
    GitOperationError,
    GitService,
    LocalConfigStore,
    MetadataStore,
    NotFoundError,
    PluginManifest,
    ProgramDialog,
    Project,
    Repo,
    RequirementsTreeWidget,
    UkoreHubError,
    confirm_action,
    plugin_source,
    save_image_asset,
)
from plugins.core.project_editor.dialogs import ConnectInputPathDialog, CustomPathEditDialog
from plugins.core.project_editor.external_plugin_catalog import CatalogEntry, ExternalPluginCatalog
from plugins.core.project_editor.external_plugin_dialog import ExternalPluginCatalogEntryDialog
from plugins.core.project_editor.pipeline_store import CustomPath, PipelineStore, RepoRef

_UI_FILE = Path(__file__).parent / "ProjectEditorSettingsWindow.ui"

_OWN_CUSTOM_PATH_LABELS = ("Custom Path Name", "Path")
_CONNECTED_CUSTOM_PATH_LABELS = ("Custom Path Name", "Repo Name", "Relative Path")
_ENABLE_PLUGINS_TABLE_LABELS = ("", "External Plugin", "Requires", "Info")

# Matches external_plugin_catalog.py's own _CATALOG_KEY and PLUGIN_ID — the
# "Repo Enable Plugins and Programs" tab still reads the raw catalog dict
# directly (get_project_plugin_data) rather than going through the shared
# ExternalPluginCatalog instance, same as before this merge — only the
# "Program and External Plugin Database" tab's CRUD needs that class.
_EXTERNAL_PLUGINS_ID = "external_plugins"
_EXTERNAL_CATALOG_KEY = "catalog"
_NOT_CLONED_INFO = "Not installed — check to clone"
_PENDING_RESTART_INFO = "Installed — restart UkoreHub to activate"
_BROKEN_CLONE_INFO = "Broken clone — fix via Settings > Project > Project Editor Settings"


class ProjectEditorSettingsPage(QWidget):
    """Settings > Project > "Project Editor Settings" — the single merged
    Settings tab, replacing the three that used to exist separately
    (CustomPathsSettingsPage, ProjectDatabasePage, RepoSettingsPage), per
    the user's own 2026-09-01 request after hand-merging their three
    separate .ui files (CustomPathWindow.ui, ProjectDatabaseWindow.ui,
    RepoSettingsWindow.ui) into one ProjectEditorSettingsWindow.ui — a
    single QTabWidget with four sub-tabs, loaded here via the same
    QUiLoader pattern project_editor_page.py uses for
    ProjectEditorTabWindows.ui. Each sub-tab keeps the exact widget names
    (and therefore the exact logic) its old standalone page used:

    - "Repo Database" — Repositories Database
      (tableWidget_project_repositories_database), formerly one of
      ProjectDatabasePage's three groupboxes.
    - "Program and External Plugin Database" — External Plugins Database
      (tableWidget_external_plugin_database) and Program Database
      (tableWidget_project_program_database), the other two of
      ProjectDatabasePage's groupboxes.
    - "Repo Enable Plugins and Programs" — formerly RepoSettingsPage:
      Repositories picker (tableWidget_repositories), Enable Programs
      (groupBox / a RequirementsTreeWidget swapped in for the .ui's
      placeholder table), Enable Plugins (tableWidget_external_enable_plugins).
    - "Custom Paths" — formerly CustomPathsSettingsPage: Connected Custom
      Path (tableWidget_connected_custom_path) and Create This Repo Custom
      Path (tableWidget_currrent_repo_custom_path). Unlike the old
      standalone page, there's no empty-state label to swap in when no
      repo is active — the merged .ui has no such widget — so with no
      active project/repo this tab's tables are just left empty.

    Self-persists on every edit, same convention every one of the three old
    pages used — no separate Save button anywhere in this tab."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        pipeline_store: PipelineStore,
        catalog: ExternalPluginCatalog,
        plugin_catalog: list[DiscoveredPlugin],
        add_repo: Callable[[], None],
        rename_repo: Callable[[str], None],
        delete_repo: Callable[[str], None],
        git_service: GitService,
        plugins_root: Path,
    ):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self.pipeline_store = pipeline_store
        self.catalog = catalog
        self._plugin_by_id = {plugin.manifest.id: plugin for plugin in plugin_catalog}
        self._plugin_by_folder = {
            plugin.dir_path.name: plugin for plugin in plugin_catalog if plugin_source(plugin) == "repo"
        }
        self._plugin_catalog = plugin_catalog
        self._git_service = git_service
        self._plugins_root = Path(plugins_root)
        self._add_repo_cb = add_repo
        self._rename_repo_cb = rename_repo
        self._delete_repo_cb = delete_repo

        # -- Repo Database / Program and External Plugin Database state --
        self._external_entries: list[CatalogEntry] = []
        self._repo_database_ids: list[str] = []

        # -- Repo Enable Plugins and Programs state --
        self._item_by_plugin_id: dict[str, QTableWidgetItem] = {}
        self._requirements_tree: RequirementsTreeWidget | None = None
        self._loading_plugins = False
        self._project: Project | None = None
        self._selected_repo: Repo | None = None
        self._selected_repo_id: str | None = None
        self._enable_repo_ids: list[str] = []

        # -- Custom Paths state --
        self._project_id: str | None = None
        self._repo_id: str | None = None
        self._custom_paths: list[CustomPath] = []
        self._connections: list[RepoRef] = []

        loader = QUiLoader()
        ui_file = QFile(str(_UI_FILE))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        find = self.ui.findChild

        # -- Repo Database tab --
        self.repo_database_table: QTableWidget = find(QTableWidget, "tableWidget_project_repositories_database")
        self._setup_database_table(self.repo_database_table, ["Name"])
        find(QPushButton, "pushButton_add_repo").clicked.connect(self._on_add_repo)
        find(QPushButton, "pushButton_edit_repo").clicked.connect(self._on_edit_repo)
        find(QPushButton, "pushButton_remove_repo").clicked.connect(self._on_remove_repo)

        # -- Program and External Plugin Database tab --
        self.plugin_table: QTableWidget = find(QTableWidget, "tableWidget_external_plugin_database")
        self._setup_database_table(self.plugin_table, ["Name", "Requires"])
        find(QPushButton, "pushButton_add_plugin_repo").clicked.connect(self._on_add_plugin)
        find(QPushButton, "pushButton_edit_plugin_repo").clicked.connect(self._on_edit_plugin)
        find(QPushButton, "pushButton_remove_plugin_repo").clicked.connect(self._on_remove_plugin)

        self.program_table: QTableWidget = find(QTableWidget, "tableWidget_project_program_database")
        self._setup_database_table(self.program_table, ["Name", "Versions"])
        find(QPushButton, "pushButton_add_program").clicked.connect(self._on_add_program)
        find(QPushButton, "pushButton_edit_program").clicked.connect(self._on_edit_program)
        find(QPushButton, "pushButton_remove_program").clicked.connect(self._on_remove_program)

        # -- Repo Enable Plugins and Programs tab --
        self._repo_table: QTableWidget = find(QTableWidget, "tableWidget_repositories")
        self._repo_table.setColumnCount(1)
        self._repo_table.setHorizontalHeaderLabels(["Repository"])
        self._repo_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._repo_table.verticalHeader().setVisible(False)
        self._repo_table.horizontalHeader().setStretchLastSection(True)
        self._repo_table.itemSelectionChanged.connect(self._on_repo_selection_changed)

        self._requirements_group: QGroupBox = find(QGroupBox, "groupBox")
        self._requirements_layout = self._requirements_group.layout()
        placeholder_table = find(QTableWidget, "tableWidget_project_enable_program")
        self._requirements_layout.removeWidget(placeholder_table)
        placeholder_table.deleteLater()

        self._external_table: QTableWidget = find(QTableWidget, "tableWidget_external_enable_plugins")
        self._setup_enable_plugins_table()
        self._external_table.itemChanged.connect(self._on_plugin_item_changed)

        # -- Custom Paths tab --
        self.connected_table: QTableWidget = find(QTableWidget, "tableWidget_connected_custom_path")
        self.current_repo_table: QTableWidget = find(QTableWidget, "tableWidget_currrent_repo_custom_path")
        self.connected_add_button: QPushButton = find(QPushButton, "pushButton_connected_custom_path_add")
        self.connected_remove_button: QPushButton = find(QPushButton, "pushButton_connected_custom_path_remove")
        self.connected_edit_button: QPushButton = find(QPushButton, "pushButton_connected_custom_path_edit")
        self.current_repo_add_button: QPushButton = find(QPushButton, "pushButton_currrent_repo_custom_path_add")
        self.current_repo_remove_button: QPushButton = find(QPushButton, "pushButton_currrent_repo_custom_path_remove")
        self.current_repo_edit_button: QPushButton = find(QPushButton, "pushButton_currrent_repo_custom_path_edit")

        self._setup_custom_path_table(self.current_repo_table, _OWN_CUSTOM_PATH_LABELS)
        self._setup_custom_path_table(self.connected_table, _CONNECTED_CUSTOM_PATH_LABELS)

        self.current_repo_table.itemSelectionChanged.connect(self._on_current_repo_selection_changed)
        self.connected_table.itemSelectionChanged.connect(self._on_connected_selection_changed)
        self._on_current_repo_selection_changed()
        self._on_connected_selection_changed()

        self.current_repo_add_button.clicked.connect(self._on_current_repo_add)
        self.current_repo_edit_button.clicked.connect(self._on_current_repo_edit)
        self.current_repo_remove_button.clicked.connect(self._on_current_repo_remove)
        self.connected_add_button.clicked.connect(self._on_connect)
        self.connected_edit_button.clicked.connect(self._on_edit_connection)
        self.connected_remove_button.clicked.connect(self._on_remove_connection)

        self.refresh()

    def refresh(self) -> None:
        """Re-reads everything this merged tab shows for the active
        project/repo. Called on construction and via
        SettingsTabSpec.on_activated."""
        self._refresh_programs()
        self._refresh_plugin_database()
        self._refresh_repo_database()
        self._refresh_enable_tab()
        self._refresh_custom_paths()

    def _active_project_id(self) -> str | None:
        return self.local_config_store.active_project_id

    @staticmethod
    def _setup_database_table(table: QTableWidget, headers: list[str]) -> None:
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for column in range(1, len(headers)):
            header.setSectionResizeMode(column, QHeaderView.Stretch)

    # ======================================================================
    # Program Database
    # ======================================================================

    def _refresh_programs(self) -> None:
        table = self.program_table
        table.setRowCount(0)
        project_id = self._active_project_id()
        if project_id is None:
            return
        programs = self.store.list_programs(project_id)
        table.setRowCount(len(programs))
        for row, program in enumerate(programs):
            name_item = QTableWidgetItem(program.name)
            name_item.setData(Qt.UserRole, program.id)
            icon_path = self.store.resolve_program_icon_path(program)
            if icon_path and icon_path.exists():
                name_item.setIcon(QIcon(str(icon_path)))
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, QTableWidgetItem(", ".join(program.versions)))

    def _selected_program_id(self) -> str | None:
        row = self.program_table.currentRow()
        if row < 0:
            return None
        item = self.program_table.item(row, 0)
        return item.data(Qt.UserRole) if item is not None else None

    def _on_add_program(self) -> None:
        project_id = self._active_project_id()
        if project_id is None:
            QMessageBox.information(self, "Add Program", "Select a project first.")
            return
        dialog = ProgramDialog(self)
        if not dialog.exec():
            return
        try:
            program = self.store.add_program(project_id, dialog.name(), dialog.description(), dialog.versions())
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Add Program", str(exc))
            self._refresh_programs()
            return
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Add Program", str(exc))
            return
        if dialog.chosen_icon_path():
            self._save_program_icon(project_id, program.id, dialog.chosen_icon_path())
        self._refresh_programs()

    def _on_edit_program(self) -> None:
        project_id = self._active_project_id()
        program_id = self._selected_program_id()
        if project_id is None or not program_id:
            QMessageBox.information(self, "Edit", "Select a program first.")
            return
        program = self.store.get_program(project_id, program_id)
        dialog = ProgramDialog(
            self,
            name=program.name,
            versions=program.versions,
            description=program.description,
            icon_path=self.store.resolve_program_icon_path(program),
        )
        if not dialog.exec():
            return
        try:
            self.store.edit_program(
                project_id, program_id, name=dialog.name(), description=dialog.description(), versions=dialog.versions()
            )
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Edit Program", str(exc))
            self._refresh_programs()
            return
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Edit Program", str(exc))
            return
        if dialog.chosen_icon_path():
            self._save_program_icon(project_id, program_id, dialog.chosen_icon_path())
        self._refresh_programs()

    def _on_remove_program(self) -> None:
        project_id = self._active_project_id()
        program_id = self._selected_program_id()
        if project_id is None or not program_id:
            QMessageBox.information(self, "Remove", "Select a program first.")
            return
        project = self.store.get_project(project_id)
        program = self.store.get_program(project_id, program_id)
        if not confirm_action(
            self,
            "Remove Program",
            f"Delete '{program.name}' from '{project.name}''s Program Database?\n\n"
            "Repos that require it will keep referencing it by ID until re-edited. This cannot be undone.",
        ):
            return
        try:
            self.store.delete_program(project_id, program_id)
        except ConflictError as exc:
            self.store.load()
            QMessageBox.warning(self, "Remove Program", str(exc))
        self._refresh_programs()

    def _save_program_icon(self, project_id: str, program_id: str, source_path) -> None:
        filename = save_image_asset(
            self, source_path=source_path, dest_dir=self.store.program_icons_dir, asset_id=program_id
        )
        if filename is not None:
            self.store.set_program_icon(project_id, program_id, filename)

    # ======================================================================
    # External Plugins Database
    # ======================================================================

    def _refresh_plugin_database(self) -> None:
        self._external_entries = self.catalog.list_entries()
        table = self.plugin_table
        table.setRowCount(len(self._external_entries))
        for row, entry in enumerate(self._external_entries):
            name_item = QTableWidgetItem(entry.name)
            name_item.setData(Qt.UserRole, entry.id)
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, QTableWidgetItem(self._requires_label(entry)))

    def _requires_label(self, entry: CatalogEntry) -> str:
        plugin = self._plugin_by_folder.get(entry.folder_name)
        if plugin is None or not plugin.manifest.requires:
            return ""
        names = [
            self._plugin_by_id[req_id].manifest.name if req_id in self._plugin_by_id else req_id
            for req_id in plugin.manifest.requires
        ]
        return ", ".join(names)

    def _selected_external_entry(self) -> CatalogEntry | None:
        row = self.plugin_table.currentRow()
        if row < 0 or row >= len(self._external_entries):
            return None
        return self._external_entries[row]

    def _on_add_plugin(self) -> None:
        dialog = ExternalPluginCatalogEntryDialog(self)
        if not dialog.exec():
            return
        try:
            self.catalog.add_entry(dialog.name(), dialog.git_url(), dialog.folder_name())
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Add External Plugin", str(exc))
            return
        self._refresh_plugin_database()

    def _on_edit_plugin(self) -> None:
        entry = self._selected_external_entry()
        if entry is None:
            QMessageBox.information(self, "Edit", "Select exactly one entry first.")
            return
        dialog = ExternalPluginCatalogEntryDialog(
            self, name=entry.name, git_url=entry.git_url, folder_name=entry.folder_name
        )
        if not dialog.exec():
            return
        try:
            self.catalog.edit_entry(
                entry.id, name=dialog.name(), git_url=dialog.git_url(), folder_name=dialog.folder_name()
            )
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Edit External Plugin", str(exc))
            return
        self._refresh_plugin_database()

    def _on_remove_plugin(self) -> None:
        entry = self._selected_external_entry()
        if entry is None:
            QMessageBox.information(self, "Remove", "Select exactly one entry first.")
            return
        if not confirm_action(
            self,
            "Remove External Plugin",
            f"Remove '{entry.name}' from this project's External Plugins catalog?\n\n"
            "This only removes the catalog entry — any already-cloned folder on disk is left untouched.",
        ):
            return
        self.catalog.delete_entry(entry.id)
        self._refresh_plugin_database()

    # ======================================================================
    # Repositories Database
    # ======================================================================

    def _refresh_repo_database(self) -> None:
        table = self.repo_database_table
        table.setRowCount(0)
        self._repo_database_ids = []
        project_id = self._active_project_id()
        if project_id is None:
            return
        try:
            project = self.store.get_project(project_id)
        except NotFoundError:
            return
        table.setRowCount(len(project.repos))
        for row, repo in enumerate(project.repos):
            self._repo_database_ids.append(repo.id)
            name_item = QTableWidgetItem(repo.name)
            name_item.setData(Qt.UserRole, repo.id)
            table.setItem(row, 0, name_item)

    def _selected_database_repo_id(self) -> str | None:
        row = self.repo_database_table.currentRow()
        if row < 0 or row >= len(self._repo_database_ids):
            return None
        return self._repo_database_ids[row]

    def _on_add_repo(self) -> None:
        self._add_repo_cb()
        self._refresh_repo_database()

    def _on_edit_repo(self) -> None:
        repo_id = self._selected_database_repo_id()
        if repo_id is None:
            QMessageBox.information(self, "Edit", "Select a repo first.")
            return
        self._rename_repo_cb(repo_id)
        self._refresh_repo_database()

    def _on_remove_repo(self) -> None:
        repo_id = self._selected_database_repo_id()
        if repo_id is None:
            QMessageBox.information(self, "Remove", "Select a repo first.")
            return
        self._delete_repo_cb(repo_id)
        self._refresh_repo_database()

    # ======================================================================
    # Repo Enable Plugins and Programs
    # ======================================================================

    def _setup_enable_plugins_table(self) -> None:
        table = self._external_table
        table.setColumnCount(len(_ENABLE_PLUGINS_TABLE_LABELS))
        table.setHorizontalHeaderLabels(list(_ENABLE_PLUGINS_TABLE_LABELS))
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)

    def _refresh_enable_tab(self) -> None:
        project_id = self.local_config_store.active_project_id
        if not project_id:
            self._project = None
            self._reload_repo_table()
            return
        try:
            self._project = self.store.get_project(project_id)
        except NotFoundError:
            self._project = None
        self._reload_repo_table()

    def _reload_repo_table(self) -> None:
        table = self._repo_table
        self._enable_repo_ids = []
        repos = self._project.repos if self._project is not None else []

        if self._selected_repo_id is None:
            self._selected_repo_id = self.local_config_store.active_repo_id

        table.blockSignals(True)
        table.setRowCount(len(repos))
        found_selected = False
        for row, repo in enumerate(repos):
            self._enable_repo_ids.append(repo.id)
            item = QTableWidgetItem(repo.name)
            item.setData(Qt.UserRole, repo.id)
            table.setItem(row, 0, item)
            if repo.id == self._selected_repo_id:
                table.setCurrentCell(row, 0)
                found_selected = True
        if not found_selected:
            self._selected_repo_id = repos[0].id if repos else None
            if repos:
                table.setCurrentCell(0, 0)
        table.blockSignals(False)

        self._resolve_selected_repo()
        self._rebuild_requirements_tree()
        self._rebuild_external_table()

    def _on_repo_selection_changed(self) -> None:
        row = self._repo_table.currentRow()
        self._selected_repo_id = self._enable_repo_ids[row] if 0 <= row < len(self._enable_repo_ids) else None
        self._resolve_selected_repo()
        self._rebuild_requirements_tree()
        self._rebuild_external_table()

    def _resolve_selected_repo(self) -> None:
        self._selected_repo = None
        if self._project is None or self._selected_repo_id is None:
            return
        try:
            self._selected_repo = self.store.get_repo(self._project.id, self._selected_repo_id)
        except NotFoundError:
            self._selected_repo = None

    # -- Enable Programs ------------------------------------------------------

    def _rebuild_requirements_tree(self) -> None:
        if self._requirements_tree is not None:
            self._requirements_layout.removeWidget(self._requirements_tree)
            self._requirements_tree.deleteLater()
            self._requirements_tree = None
        if self._selected_repo is None or self._project is None:
            return
        self._requirements_tree = RequirementsTreeWidget(
            store=self.store,
            project_id=self._project.id,
            selected_program_ids=self._selected_repo.required_program_ids,
            selected_program_version_pins=self._selected_repo.program_version_pins,
        )
        self._requirements_tree.itemChanged.connect(self._on_requirements_tree_changed)
        self._requirements_layout.addWidget(self._requirements_tree, 0, 0)

    def _on_requirements_tree_changed(self, _item, _column) -> None:
        if self._project is None or self._selected_repo is None or self._requirements_tree is None:
            return
        program_ids = self._requirements_tree.selected_program_ids()
        pins = self._requirements_tree.selected_program_version_pins()
        self.store.set_repo_requirements(self._project.id, self._selected_repo.id, program_ids)
        self.store.set_repo_program_version_pins(self._project.id, self._selected_repo.id, pins)
        self._selected_repo.required_program_ids = program_ids
        self._selected_repo.program_version_pins = pins

    # -- Enable Plugins -------------------------------------------------------

    def _rebuild_external_table(self) -> None:
        # Guard against itemChanged firing while we're programmatically
        # setting check states below (would otherwise re-persist a
        # half-built table on every single setItem call).
        self._loading_plugins = True
        self._external_table.setRowCount(0)
        self._item_by_plugin_id = {}
        if self._selected_repo is not None:
            required_ids = self._selected_repo.required_plugin_ids
            discovered_repo_folders: set[str] = set()
            for plugin in self._plugin_catalog:
                if plugin_source(plugin) != "repo":
                    continue
                # source == "repo" (External) — every discovered one is a
                # choice, whether or not it's currently required. Core
                # plugins are always on and have nothing to toggle, so they
                # never get a row here.
                discovered_repo_folders.add(plugin.dir_path.name)
                self._add_plugin_row(plugin, required_ids)
            self._add_pending_external_items(discovered_repo_folders, required_ids)
        self._loading_plugins = False

    def _add_plugin_row(self, plugin: DiscoveredPlugin, required_ids: list[str]) -> None:
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        checkbox_item.setData(Qt.UserRole, plugin.manifest.id)
        checkbox_item.setCheckState(Qt.Checked if plugin.manifest.id in required_ids else Qt.Unchecked)
        self._append_enable_row(checkbox_item, plugin.manifest.name, self._requires_text(plugin))
        self._item_by_plugin_id[plugin.manifest.id] = checkbox_item

    def _requires_text(self, plugin: DiscoveredPlugin) -> str:
        """'X, Y', resolving each required id to its discovered manifest
        name via self._plugin_by_id (built from the full plugin_catalog at
        construction, so this covers Core/External requirements alike) —
        '' if plugin.manifest.requires is empty. Always visible (not just
        on check, unlike the _confirm_and_enable_requirements prompt below)
        so a dependency is known before you check anything."""
        if not plugin.manifest.requires:
            return ""
        return ", ".join(
            self._plugin_by_id[req_id].manifest.name if req_id in self._plugin_by_id else req_id
            for req_id in plugin.manifest.requires
        )

    def _append_enable_row(self, checkbox_item: QTableWidgetItem, name: str, requires: str, info: str = "") -> None:
        table = self._external_table
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, checkbox_item)
        name_item = QTableWidgetItem(name)
        name_item.setFlags(Qt.ItemIsEnabled)
        table.setItem(row, 1, name_item)
        requires_item = QTableWidgetItem(requires)
        requires_item.setFlags(Qt.ItemIsEnabled)
        table.setItem(row, 2, requires_item)
        info_item = QTableWidgetItem(info)
        info_item.setFlags(Qt.ItemIsEnabled)
        table.setItem(row, 3, info_item)

    def _add_pending_external_items(self, discovered_repo_folders: set[str], required_ids: list[str]) -> None:
        """A per-project catalog entry (external_plugin_catalog.py) that
        this session's plugin discovery hasn't picked up (see loader.py's
        discover_plugins, run once at app startup) — split by actual
        on-disk state, since "not discovered yet" covers three different
        situations:
        - Not cloned at all: checkable — checking it clones it right here
          (see _on_catalog_entry_checked) instead of sending the user to
          Settings > Account > Plugins first.
        - Cloned (by this flow or by hand) but not yet discovered this
          session: shown disabled with its current required-for-this-repo
          state, since there's nothing left to do but restart.
        - A broken .git directory (GitService.is_cloned true, is_repo_root
          false): shown disabled, pointing at Project Database to fix it
          rather than silently treating it as installed."""
        for entry in sorted(self._read_external_catalog(), key=lambda e: e["name"]):
            if entry["folder_name"] in discovered_repo_folders:
                continue
            local_path = self._plugins_root / entry["folder_name"]
            if not self._git_service.is_cloned(local_path):
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_item.setData(Qt.UserRole + 1, entry["id"])
                checkbox_item.setCheckState(Qt.Unchecked)
                self._append_enable_row(checkbox_item, entry["name"], "", _NOT_CLONED_INFO)
                continue
            if not self._git_service.is_repo_root(local_path):
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.NoItemFlags)
                self._append_enable_row(checkbox_item, entry["name"], "", _BROKEN_CLONE_INFO)
                continue
            manifest = self._read_manifest_if_cloned(entry["folder_name"])
            label = manifest.name if manifest is not None else entry["name"]
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable)
            is_required = manifest is not None and manifest.id in required_ids
            checkbox_item.setCheckState(Qt.Checked if is_required else Qt.Unchecked)
            self._append_enable_row(checkbox_item, label, "", _PENDING_RESTART_INFO)

    def _read_manifest_if_cloned(self, folder_name: str) -> PluginManifest | None:
        """A raw manifest.json read/parse only — never imports or executes
        the plugin's entry_point (unlike loader.discover_plugins), since
        running a plugin's code mid-session outside the normal one-shot
        startup flow is out of scope here. Used right after cloning (to
        learn the real plugin id to mark required) and for a folder cloned
        earlier this session that's still awaiting restart."""
        manifest_path = self._plugins_root / folder_name / "manifest.json"
        if not manifest_path.exists():
            return None
        try:
            return PluginManifest.from_dict(json.loads(manifest_path.read_text(encoding="utf-8")))
        except (OSError, ValueError, KeyError):
            return None

    def _read_external_catalog(self) -> list[dict]:
        """The active Project's own External Plugins catalog — read
        straight from self.store on every call, no caching, so an edit made
        on the "Program and External Plugin Database" tab earlier in the
        same session is picked up the next time this tab is opened."""
        if self._project is None:
            return []
        plugin_data = self.store.get_project_plugin_data(self._project.id, _EXTERNAL_PLUGINS_ID)
        return plugin_data.get(_EXTERNAL_CATALOG_KEY, [])

    def _on_catalog_entry_checked(self, item: QTableWidgetItem, entry_id: str) -> None:
        """Handles a check-state change on a not-yet-cloned catalog entry
        row (see _add_pending_external_items) — the only state such a row
        can be in, so unchecking it (e.g. immediately after a failed clone
        reverts it below) needs no persistence of its own; there was never
        anything installed or required to undo."""
        if item.checkState() != Qt.Checked:
            return

        entry = next((e for e in self._read_external_catalog() if e.get("id") == entry_id), None)
        if entry is None:
            self._set_item_checked(item, False)
            return

        git_url = entry.get("git_url", "")
        if not git_url:
            QMessageBox.warning(
                self,
                "Clone Plugin",
                f"'{entry['name']}' has no Git URL set — edit it via "
                "Settings > Project > Project Editor Settings first.",
            )
            self._set_item_checked(item, False)
            return

        local_path = self._plugins_root / entry["folder_name"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self._git_service.clone(git_url, local_path)
        except GitOperationError as exc:
            QMessageBox.warning(self, "Clone Plugin", str(exc))
            self._set_item_checked(item, False)
            return
        finally:
            QApplication.restoreOverrideCursor()

        manifest = self._read_manifest_if_cloned(entry["folder_name"])
        if manifest is None:
            QMessageBox.warning(
                self,
                "Clone Plugin",
                f"Cloned '{entry['name']}', but its manifest.json is missing or invalid.",
            )
            self._rebuild_external_table()
            return

        required_ids = list(self._selected_repo.required_plugin_ids)
        if manifest.id not in required_ids:
            required_ids.append(manifest.id)
            self.store.set_repo_required_plugin_ids(self._project.id, self._selected_repo.id, required_ids)
            self._selected_repo.required_plugin_ids = required_ids

        QMessageBox.information(
            self,
            "Clone Plugin",
            f"Cloned '{manifest.name}'. It's marked as required for this repo — "
            "restart UkoreHub for it to actually load.",
        )
        self._rebuild_external_table()

    def _on_plugin_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 0 or self._loading_plugins or self._project is None or self._selected_repo is None:
            return

        entry_id = item.data(Qt.UserRole + 1)
        if entry_id is not None:
            self._on_catalog_entry_checked(item, entry_id)
            return

        plugin_id = item.data(Qt.UserRole)
        if plugin_id is None:
            return

        if item.checkState() == Qt.Checked:
            if not self._confirm_and_enable_requirements(plugin_id):
                self._set_item_checked(item, False)
                return
        else:
            if not self._confirm_disable(plugin_id):
                self._set_item_checked(item, True)
                return

        self._persist_required_plugin_ids()

    def _set_item_checked(self, item: QTableWidgetItem, checked: bool) -> None:
        # Guarded so this programmatic change doesn't re-enter
        # _on_plugin_item_changed (it fires itemChanged same as a user click).
        self._loading_plugins = True
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self._loading_plugins = False

    def _enabled_plugin_ids(self) -> set[str]:
        """Plugin ids currently in effect for the repo being edited: every
        always-on Core plugin plus every checked External row."""
        enabled = {plugin.manifest.id for plugin in self._plugin_catalog if plugin_source(plugin) == "core"}
        for row in range(self._external_table.rowCount()):
            item = self._external_table.item(row, 0)
            if item is not None and item.checkState() == Qt.Checked:
                plugin_id = item.data(Qt.UserRole)
                if plugin_id is not None:
                    enabled.add(plugin_id)
        return enabled

    def _requires_closure(self, plugin_id: str) -> list[str]:
        """Transitive requirement ids for plugin_id (not including
        plugin_id itself), deepest-first. Ids that aren't in the discovered
        plugin catalog are silently skipped — nothing to enable for a
        requirement that doesn't exist."""
        seen: set[str] = set()
        ordered: list[str] = []

        def visit(pid: str) -> None:
            plugin = self._plugin_by_id.get(pid)
            if plugin is None:
                return
            for req_id in plugin.manifest.requires:
                if req_id in seen:
                    continue
                seen.add(req_id)
                visit(req_id)
                ordered.append(req_id)

        visit(plugin_id)
        return ordered

    def _confirm_and_enable_requirements(self, plugin_id: str) -> bool:
        """Called after `plugin_id`'s own checkbox is already checked.
        Returns False (caller should revert) only if the user declines to
        also enable its unmet requirements; True if there was nothing to
        enable or the user agreed."""
        enabled = self._enabled_plugin_ids()
        missing_ids = [req_id for req_id in self._requires_closure(plugin_id) if req_id not in enabled]
        missing_items = [self._item_by_plugin_id[req_id] for req_id in missing_ids if req_id in self._item_by_plugin_id]
        if not missing_items:
            return True

        plugin_name = self._plugin_by_id[plugin_id].manifest.name
        names = "\n".join(f"- {self._plugin_by_id[req_id].manifest.name}" for req_id in missing_ids if req_id in self._plugin_by_id)
        confirm = QMessageBox.question(
            self,
            "Enable Required Plugins",
            f"'{plugin_name}' requires the following plugin(s), currently disabled for this repo:\n\n"
            f"{names}\n\nEnable them along with '{plugin_name}'?",
        )
        if confirm != QMessageBox.Yes:
            return False

        for req_item in missing_items:
            self._set_item_checked(req_item, True)
        return True

    def _confirm_disable(self, plugin_id: str) -> bool:
        """Called after `plugin_id`'s own checkbox is already unchecked.
        Returns False (caller should revert) only if the user declines to
        proceed after being warned some other still-enabled plugin requires
        it; True if nothing depends on it or the user confirmed anyway."""
        enabled = self._enabled_plugin_ids()
        dependents = [
            plugin.manifest.name
            for plugin in self._plugin_catalog
            if plugin.manifest.id in enabled and plugin_id in plugin.manifest.requires
        ]
        if not dependents:
            return True

        plugin_name = self._plugin_by_id[plugin_id].manifest.name
        names = "\n".join(f"- {name}" for name in dependents)
        confirm = QMessageBox.question(
            self,
            "Disable Plugin",
            f"Disabling '{plugin_name}' will break the following plugin(s), which require it:\n\n"
            f"{names}\n\nDisable '{plugin_name}' anyway?",
        )
        return confirm == QMessageBox.Yes

    def _persist_required_plugin_ids(self) -> None:
        required_ids = []
        for row in range(self._external_table.rowCount()):
            item = self._external_table.item(row, 0)
            if item is None or item.checkState() != Qt.Checked:
                continue
            plugin_id = item.data(Qt.UserRole)
            if plugin_id:
                required_ids.append(plugin_id)
        self.store.set_repo_required_plugin_ids(self._project.id, self._selected_repo.id, required_ids)
        self._selected_repo.required_plugin_ids = required_ids

    # ======================================================================
    # Custom Paths
    # ======================================================================

    @staticmethod
    def _setup_custom_path_table(table: QTableWidget, column_labels: tuple[str, ...]) -> None:
        table.setColumnCount(len(column_labels))
        table.setHorizontalHeaderLabels(list(column_labels))
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)

    def _refresh_custom_paths(self) -> None:
        """Re-resolves the active project/repo from local_config_store and
        rebuilds both Custom Paths tables. Unlike the old standalone
        CustomPathsSettingsPage, there's no empty-state label to show when
        no repo is active (the merged .ui has no such widget) — the tables
        are just left empty."""
        project_id = self.local_config_store.active_project_id
        repo_id = self.local_config_store.active_repo_id
        if project_id and repo_id:
            try:
                self.store.get_repo(project_id, repo_id)
            except NotFoundError:
                project_id = None
        if not project_id or not repo_id:
            self._project_id = None
            self._repo_id = None
            self._custom_paths = []
            self._connections = []
            self._rebuild_current_repo_table()
            self._rebuild_connected_table()
            return
        self._project_id = project_id
        self._repo_id = repo_id
        self._custom_paths = self.pipeline_store.get_custom_paths(project_id, repo_id)
        self._connections = self.pipeline_store.get_inputs(project_id, repo_id)
        self._rebuild_current_repo_table()
        self._rebuild_connected_table()

    def _repo_root(self) -> Path | None:
        if self._project_id is None or self._repo_id is None:
            return None
        try:
            repo = self.store.get_repo(self._project_id, self._repo_id)
        except NotFoundError:
            return None
        return Path(self.local_config_store.workspace_root) / repo.local_path

    # -- "Create This Repo Custom Path" ------------------------------------

    def _rebuild_current_repo_table(self) -> None:
        table = self.current_repo_table
        table.setRowCount(len(self._custom_paths))
        for row, custom_path in enumerate(self._custom_paths):
            name_item = QTableWidgetItem(custom_path.label)
            name_item.setData(Qt.UserRole, custom_path.id)
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, QTableWidgetItem(custom_path.path))
        self._on_current_repo_selection_changed()

    def _on_current_repo_selection_changed(self) -> None:
        has_selection = bool(self.current_repo_table.selectedItems())
        self.current_repo_edit_button.setEnabled(has_selection)
        self.current_repo_remove_button.setEnabled(has_selection)

    def _selected_current_repo_index(self) -> int | None:
        items = self.current_repo_table.selectedItems()
        if not items:
            return None
        row = items[0].row()
        custom_path_id = self.current_repo_table.item(row, 0).data(Qt.UserRole)
        for index, custom_path in enumerate(self._custom_paths):
            if custom_path.id == custom_path_id:
                return index
        return None

    def _on_current_repo_add(self) -> None:
        repo_root = self._repo_root()
        if repo_root is None:
            return
        dialog = CustomPathEditDialog(self, repo_root=repo_root, title="Add Custom Path")
        if not dialog.exec():
            return
        label, path = dialog.result_values()
        custom_paths = list(self._custom_paths) + [CustomPath(id=CustomPath.new_id(), label=label, path=path)]
        self._save_custom_paths(custom_paths)

    def _on_current_repo_edit(self) -> None:
        index = self._selected_current_repo_index()
        if index is None:
            return
        repo_root = self._repo_root()
        if repo_root is None:
            return
        current = self._custom_paths[index]
        dialog = CustomPathEditDialog(self, repo_root=repo_root, label=current.label, path=current.path, title="Edit Custom Path")
        if not dialog.exec():
            return
        label, path = dialog.result_values()
        custom_paths = list(self._custom_paths)
        custom_paths[index] = CustomPath(id=current.id, label=label, path=path)
        self._save_custom_paths(custom_paths)

    def _on_current_repo_remove(self) -> None:
        index = self._selected_current_repo_index()
        if index is None:
            return
        custom_paths = list(self._custom_paths)
        del custom_paths[index]
        self._save_custom_paths(custom_paths)

    def _save_custom_paths(self, custom_paths: list[CustomPath]) -> None:
        self.pipeline_store.set_custom_paths(self._project_id, self._repo_id, custom_paths)
        self._custom_paths = custom_paths
        self._rebuild_current_repo_table()
        self._rebuild_connected_table()  # this repo's own paths also show up there

    # -- "Connected Custom Path" --------------------------------------------

    def _rebuild_connected_table(self) -> None:
        table = self.connected_table
        if self._project_id is None or self._repo_id is None:
            table.setRowCount(0)
            self._on_connected_selection_changed()
            return
        try:
            repo_name = self.store.get_repo(self._project_id, self._repo_id).name
        except NotFoundError:
            repo_name = ""

        rows: list[tuple[str, str, str, tuple]] = []
        for custom_path in self._custom_paths:
            rows.append((custom_path.label, repo_name, f"{repo_name}/{custom_path.path}", ("own", custom_path.id)))
        for index, ref in enumerate(self._connections):
            try:
                target_name = self.store.get_repo(ref.project_id, ref.repo_id).name
            except NotFoundError:
                target_name = "(deleted repo)"
            custom_path = self.pipeline_store.get_custom_path(ref.project_id, ref.repo_id, ref.custom_path_id)
            if custom_path is not None:
                label = custom_path.label
                relative = f"{target_name}/{custom_path.path}"
            else:
                label = "(deleted custom path)"
                relative = "—"
            rows.append((label, target_name, relative, ("connection", index)))

        table.setRowCount(len(rows))
        for row, (name, repo, relative, tag) in enumerate(rows):
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, tag)
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, QTableWidgetItem(repo))
            table.setItem(row, 2, QTableWidgetItem(relative))
        self._on_connected_selection_changed()

    def _selected_connected_tag(self):
        items = self.connected_table.selectedItems()
        if not items:
            return None
        row = items[0].row()
        name_item = self.connected_table.item(row, 0)
        return name_item.data(Qt.UserRole) if name_item is not None else None

    def _on_connected_selection_changed(self) -> None:
        tag = self._selected_connected_tag()
        is_connection = isinstance(tag, tuple) and tag[0] == "connection"
        self.connected_edit_button.setEnabled(is_connection)
        self.connected_remove_button.setEnabled(is_connection)

    def _run_connect_dialog(self, *, initial_ref: RepoRef | None, title: str) -> tuple[str, str, str, str] | None:
        """Shared by _on_connect (creating a new connection) and
        _on_edit_connection (editing an existing one, pre-filled via
        ConnectInputPathDialog's initial_ref) — constructs the dialog,
        runs it, and returns (target_project_id, target_repo_id,
        target_custom_path_id, direction), or None if it was cancelled or
        nothing valid was picked."""
        if self._project_id is None or self._repo_id is None:
            return None
        dialog = ConnectInputPathDialog(
            self,
            store=self.store,
            pipeline_store=self.pipeline_store,
            exclude_project_id=self._project_id,
            exclude_repo_id=self._repo_id,
            initial_ref=initial_ref,
            title=title,
        )
        if not dialog.exec():
            return None
        selected = dialog.selected_ref()
        if selected is None:
            return None
        target_project_id, target_repo_id, target_custom_path_id = selected
        return target_project_id, target_repo_id, target_custom_path_id, dialog.selected_direction()

    def _on_connect(self) -> None:
        result = self._run_connect_dialog(initial_ref=None, title="Connect Input Path")
        if result is None:
            return
        target_project_id, target_repo_id, target_custom_path_id, direction = result
        if any(
            ref.project_id == target_project_id
            and ref.repo_id == target_repo_id
            and ref.custom_path_id == target_custom_path_id
            and ref.direction == direction
            for ref in self._connections
        ):
            return  # already connected (same target repo + same custom path + same direction)
        connections = list(self._connections)
        connections.append(
            RepoRef(
                project_id=target_project_id,
                repo_id=target_repo_id,
                custom_path_id=target_custom_path_id,
                direction=direction,
            )
        )
        self._save_connections(connections)

    def _on_edit_connection(self) -> None:
        tag = self._selected_connected_tag()
        if not (isinstance(tag, tuple) and tag[0] == "connection"):
            return
        index = tag[1]
        if not (0 <= index < len(self._connections)):
            return
        result = self._run_connect_dialog(initial_ref=self._connections[index], title="Edit Input Path")
        if result is None:
            return
        target_project_id, target_repo_id, target_custom_path_id, direction = result
        if any(
            i != index
            and ref.project_id == target_project_id
            and ref.repo_id == target_repo_id
            and ref.custom_path_id == target_custom_path_id
            and ref.direction == direction
            for i, ref in enumerate(self._connections)
        ):
            QMessageBox.information(self, "Edit Input Path", "This repo is already connected the same way.")
            return
        connections = list(self._connections)
        connections[index] = RepoRef(
            project_id=target_project_id,
            repo_id=target_repo_id,
            custom_path_id=target_custom_path_id,
            direction=direction,
        )
        self._save_connections(connections)

    def _on_remove_connection(self) -> None:
        tag = self._selected_connected_tag()
        if not (isinstance(tag, tuple) and tag[0] == "connection"):
            return
        index = tag[1]
        if not (0 <= index < len(self._connections)):
            return
        connections = list(self._connections)
        del connections[index]
        self._save_connections(connections)

    def _save_connections(self, connections: list[RepoRef]) -> None:
        self.pipeline_store.set_inputs(self._project_id, self._repo_id, connections)
        self._connections = connections
        self._rebuild_connected_table()
