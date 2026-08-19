from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plugin_api import LocalConfigStore, MetadataStore, NotFoundError, show_exclusive
from plugins.core.project_editor.pipeline_store import CustomPath, PipelineStore, RepoRef

_UI_FILE = Path(__file__).parent / "CustomPathWindow.ui"
_OWN_COLUMN_LABELS = ("Custom Path Name", "Path")
_CONNECTED_COLUMN_LABELS = ("Custom Path Name", "Repo Name", "Relative Path")


class ConnectInputPathDialog(QDialog):
    """Compact single-window replacement for the old two-dialog
    RepoPickerDialog -> CustomPathPickerDialog flow that used to live behind
    the old node graph's "Connect Pipeline Input Path..." node context-menu
    action (removed 2026-07-19, the graph itself removed later, 2026-08-19)
    — one repo combo
    box plus one custom-path combo box, refreshed together in a single small
    window instead of two separate modal round-trips through a heavy
    thumbnail-card picker. Also picks this connection's `direction`
    (added 2026-07-19) — purely cosmetic (see RepoRef.direction's
    docstring): it only decides which end of the drawn edge gets the
    arrowhead in the Graph View, never the layout/topology."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        pipeline_store: PipelineStore,
        exclude_project_id: str,
        exclude_repo_id: str,
        initial_ref: RepoRef | None = None,
        title: str = "Connect Input Path",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(380, 220)
        self._store = store
        self._pipeline_store = pipeline_store
        self._repo_ids: list[tuple[str, str]] = []
        self._custom_paths: list[CustomPath] = []

        self.repo_combo = QComboBox()
        for project in store.list_projects():
            for repo in project.repos:
                if project.id == exclude_project_id and repo.id == exclude_repo_id:
                    continue
                self.repo_combo.addItem(f"{project.name} / {repo.name}")
                self._repo_ids.append((project.id, repo.id))
        self.repo_combo.currentIndexChanged.connect(self._on_repo_changed)

        self.path_combo = QComboBox()

        self.input_radio = QRadioButton("Input — arrow points into this repo")
        self.input_radio.setChecked(True)
        self.output_radio = QRadioButton("Output — arrow points out to the target repo")

        self.hint_label = QLabel("")
        self.hint_label.setWordWrap(True)
        self.hint_label.setVisible(False)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Repo:"))
        layout.addWidget(self.repo_combo)
        layout.addWidget(QLabel("Custom Path:"))
        layout.addWidget(self.path_combo)
        layout.addWidget(QLabel("Direction:"))
        layout.addWidget(self.input_radio)
        layout.addWidget(self.output_radio)
        layout.addWidget(self.hint_label)
        layout.addStretch()
        layout.addWidget(self.buttons)

        if self._repo_ids:
            self._on_repo_changed(0)
            if initial_ref is not None:
                self._apply_initial_ref(initial_ref)
        else:
            self.hint_label.setText("No other repos exist yet.")
            self.hint_label.setVisible(True)
            self.repo_combo.setEnabled(False)
            self.path_combo.setEnabled(False)
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)

    def _apply_initial_ref(self, ref: RepoRef) -> None:
        """Pre-selects everything to match an existing connection — used
        when this dialog is opened to Edit one (see
        CustomPathsSettingsPage._on_edit_connection) rather than create a
        new one. A no-op for anything that can no longer be found (e.g.
        the target repo or its custom path was deleted since this
        connection was made) — the dialog just falls back to its normal
        default selection for that part."""
        for index, (project_id, repo_id) in enumerate(self._repo_ids):
            if project_id == ref.project_id and repo_id == ref.repo_id:
                self.repo_combo.setCurrentIndex(index)
                break
        for index, custom_path in enumerate(self._custom_paths):
            if custom_path.id == ref.custom_path_id:
                self.path_combo.setCurrentIndex(index)
                break
        if ref.direction == "output":
            self.output_radio.setChecked(True)
        else:
            self.input_radio.setChecked(True)

    def _on_repo_changed(self, index: int) -> None:
        self.path_combo.clear()
        self._custom_paths = []
        if not (0 <= index < len(self._repo_ids)):
            return
        project_id, repo_id = self._repo_ids[index]
        self._custom_paths = self._pipeline_store.get_custom_paths(project_id, repo_id)
        if not self._custom_paths:
            try:
                repo_name = self._store.get_repo(project_id, repo_id).name
            except NotFoundError:
                repo_name = "This repo"
            self.hint_label.setText(
                f"{repo_name} has no Custom Paths declared yet — switch to it and add one under its own "
                "Repository Setting > Custom Paths > Create This Repo Custom Path first."
            )
            self.hint_label.setVisible(True)
            self.path_combo.setEnabled(False)
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)
            return
        self.hint_label.setVisible(False)
        self.path_combo.setEnabled(True)
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(True)
        for custom_path in self._custom_paths:
            self.path_combo.addItem(f"{custom_path.label}  ({custom_path.path})")

    def selected_ref(self) -> tuple[str, str, str] | None:
        repo_index = self.repo_combo.currentIndex()
        path_index = self.path_combo.currentIndex()
        if not (0 <= repo_index < len(self._repo_ids)) or not (0 <= path_index < len(self._custom_paths)):
            return None
        project_id, repo_id = self._repo_ids[repo_index]
        return project_id, repo_id, self._custom_paths[path_index].id

    def selected_direction(self) -> str:
        return "output" if self.output_radio.isChecked() else "input"


class CustomPathEditDialog(QDialog):
    """Add/Edit dialog for one of this repo's own declared CustomPath
    entries — used by tableWidget_currrent_repo_custom_path's Add/Edit
    buttons (CustomPathWindow.ui). Replaces the old always-visible
    label/path input row + separate "Rename"/"Edit Path" row actions with a
    single small dialog, matching how ConnectInputPathDialog already
    handles the "Connected Custom Path" side."""

    def __init__(
        self,
        parent=None,
        *,
        repo_root: Path,
        label: str = "",
        path: str = "",
        title: str = "Add Custom Path",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._repo_root = repo_root

        self.label_edit = QLineEdit(label)
        self.label_edit.setPlaceholderText("Label (e.g. Character)")
        self.path_edit = QLineEdit(path)
        self.path_edit.setPlaceholderText("Path relative to this repo's root (e.g. Character)")
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._on_browse)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit, stretch=1)
        path_row.addWidget(browse_button)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Label:"))
        layout.addWidget(self.label_edit)
        layout.addWidget(QLabel("Path:"))
        layout.addLayout(path_row)
        layout.addStretch()
        layout.addWidget(self.buttons)

    def _on_browse(self) -> None:
        """Rooted at the active repo's own folder; rejects a folder picked
        from outside it, since CustomPath.path is always relative to the
        repo's own root — same rule custom_paths_settings_page.py enforced
        before this dialog existed. Auto-fills the label from the folder
        name too if the label field is still empty."""
        chosen = QFileDialog.getExistingDirectory(self, "Choose Folder", str(self._repo_root))
        if not chosen:
            return
        chosen_path = Path(chosen)
        try:
            relative = chosen_path.relative_to(self._repo_root)
        except ValueError:
            QMessageBox.information(
                self,
                "Choose Folder",
                "Pick a folder inside this repo's own root — Custom Paths are always relative to it.",
            )
            return
        self.path_edit.setText(str(relative).replace("\\", "/"))
        if not self.label_edit.text().strip():
            self.label_edit.setText(chosen_path.name)

    def _on_accept(self) -> None:
        if not self.label_edit.text().strip() or not self.path_edit.text().strip():
            QMessageBox.information(self, self.windowTitle(), "Enter both a label and a path.")
            return
        self.accept()

    def result_values(self) -> tuple[str, str]:
        return self.label_edit.text().strip(), self.path_edit.text().strip()


class CustomPathsSettingsPage(QWidget):
    """Active repo's Custom Paths tab — UI authored in Qt Designer
    (CustomPathWindow.ui) and loaded at runtime instead of being built
    widget-by-widget in code, same QUiLoader pattern
    plugins/core/explorer/browser_widget.py uses for explorer_section.ui.
    Two tables:

    - tableWidget_currrent_repo_custom_path ("Create This Repo Custom
      Path") — this repo's own declared CustomPath catalog (named
      locations other repos' pipeline refs can point at — see
      pipeline_store.py's CustomPath/RepoRef). Add/Edit open
      CustomPathEditDialog above; Remove drops the selected entry
      directly, no confirmation (unchanged from before this rewrite).
    - tableWidget_connected_custom_path ("Connected Custom Path") — every
      path this repo is "connected" to: its own CustomPath entries
      (tagged ("own", id) via Qt.UserRole on each row) *and* its outgoing
      pipeline connections (tagged ("connection", index), each a RepoRef
      pointing at another repo's declared CustomPath, driving
      ProjectGraphView._collect_edges' graph edges). Add opens
      ConnectInputPathDialog to create a new outgoing connection
      (unchanged _on_connect logic); Edit/Remove only ever act on
      ("connection", ...) rows — disabled via
      _on_connected_selection_changed whenever the selected row is one of
      this repo's own ("own", ...) entries, since those can only be
      edited/removed through the other table. Direction (input/output) is
      no longer shown as its own column here — it still round-trips
      through RepoRef.direction and ConnectInputPathDialog unchanged.

    Same self-resolving-active-repo `refresh()` pattern
    interface/shared/base_repo_settings_page.py's BaseRepoSettingsPage
    provides — scoped to a single repo, so it reads local_config_store
    itself rather than waiting for a set_repo() call MainWindow never
    makes for Settings pages."""

    def __init__(self, parent=None, *, store: MetadataStore, local_config_store: LocalConfigStore, pipeline_store: PipelineStore):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self.pipeline_store = pipeline_store
        self._project_id: str | None = None
        self._repo_id: str | None = None
        self._custom_paths: list[CustomPath] = []
        self._connections: list[RepoRef] = []

        self.empty_label = QLabel("Select a repo to see this information.")

        loader = QUiLoader()
        ui_file = QFile(str(_UI_FILE))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.ui)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)

        self.connected_table: QTableWidget = self.ui.findChild(QTableWidget, "tableWidget_connected_custom_path")
        self.current_repo_table: QTableWidget = self.ui.findChild(QTableWidget, "tableWidget_currrent_repo_custom_path")
        self.connected_add_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_connected_custom_path_add")
        self.connected_remove_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_connected_custom_path_remove")
        self.connected_edit_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_connected_custom_path_edit")
        self.current_repo_add_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_currrent_repo_custom_path_add")
        self.current_repo_remove_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_currrent_repo_custom_path_remove")
        self.current_repo_edit_button: QPushButton = self.ui.findChild(QPushButton, "pushButton_currrent_repo_custom_path_edit")

        self._setup_table(self.current_repo_table, _OWN_COLUMN_LABELS)
        self._setup_table(self.connected_table, _CONNECTED_COLUMN_LABELS)

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

    @staticmethod
    def _setup_table(table: QTableWidget, column_labels: tuple[str, ...]) -> None:
        table.setColumnCount(len(column_labels))
        table.setHorizontalHeaderLabels(list(column_labels))
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)

    def refresh(self) -> None:
        """Re-resolves the active project/repo from local_config_store and
        rebuilds both tables — called on construction and every time this
        tab becomes active (SettingsTabSpec.on_activated)."""
        project_id = self.local_config_store.active_project_id
        repo_id = self.local_config_store.active_repo_id
        if not project_id or not repo_id:
            self._project_id = None
            self._repo_id = None
            show_exclusive(self.empty_label, self.content_widget)
            return
        try:
            self.store.get_repo(project_id, repo_id)
        except NotFoundError:
            self._project_id = None
            self._repo_id = None
            show_exclusive(self.empty_label, self.content_widget)
            return
        self._project_id = project_id
        self._repo_id = repo_id
        show_exclusive(self.content_widget, self.empty_label)
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
