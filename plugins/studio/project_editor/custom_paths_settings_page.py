from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import NotFoundError
from core.store import LocalConfigStore, MetadataStore
from interface.shared.widget_helpers import show_exclusive, wrap_scrollable
from plugins.studio.project_editor.pipeline_store import CustomPath, PipelineStore, RepoRef


class ConnectInputPathDialog(QDialog):
    """Compact single-window replacement for the old two-dialog
    RepoPickerDialog -> CustomPathPickerDialog flow that used to live behind
    the Graph View's "Connect Pipeline Input Path..." node context-menu
    action (removed 2026-07-19, see project_graph_view.py) — one repo combo
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
                "Repository Setting > Custom Paths > Create Input Path first."
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


class CustomPathsSettingsPage(QWidget):
    """Active repo's Custom Paths tab, split into two sections:

    - "Create Input Path" — add/rename/edit/remove this repo's own declared
      CustomPath catalog (named locations other repos' pipeline refs can
      point at — see ProjectGraphView's now-removed add_pipeline_ref
      docstring history, pipeline_store.py's CustomPath/RepoRef). Unchanged
      from before 2026-07-19 beyond being wrapped in its own group box.
    - "Connect Input Path" — this repo's own outgoing pipeline connections
      (each a RepoRef pointing at another repo's declared CustomPath,
      driving ProjectGraphView._collect_edges' graph edges). Moved here
      2026-07-19 from the Graph View node's right-click menu, with a
      compact single-dialog picker (ConnectInputPathDialog above) replacing
      the old two-step RepoPickerDialog/CustomPathPickerDialog flow, plus
      Edit and Remove buttons per connection — there was previously no way
      to change or remove a connection at all (graph edges are
      non-interactive); Edit reopens the same dialog pre-filled via
      ConnectInputPathDialog's initial_ref (added 2026-07-19).

    Same self-resolving-active-repo `refresh()` pattern as
    interface/settings/browser_links_settings_page.py's
    BrowserLinksSettingsPage — scoped to a single repo, so it reads
    local_config_store itself rather than waiting for a set_repo() call
    MainWindow never makes for Settings pages."""

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

        # -- "Create Input Path" ------------------------------------------
        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)

        self.new_label_edit = QLineEdit()
        self.new_label_edit.setPlaceholderText("Label (e.g. Character)")
        self.new_path_edit = QLineEdit()
        self.new_path_edit.setPlaceholderText("Path relative to this repo's root (e.g. Character)")
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._on_browse_new_path)
        add_button = QPushButton("Add Custom Path")
        add_button.clicked.connect(self._on_add)
        add_row = QHBoxLayout()
        add_row.addWidget(self.new_label_edit)
        add_row.addWidget(self.new_path_edit, stretch=1)
        add_row.addWidget(browse_button)
        add_row.addWidget(add_button)

        create_hint_label = QLabel(
            "Other repos' Connect Input Path picks one of these when pointing at this repo — "
            "add at least one before another repo can reference it."
        )
        create_hint_label.setWordWrap(True)
        create_hint_label.setProperty("secondary", True)

        create_group = QGroupBox("Create Input Path")
        create_layout = QVBoxLayout(create_group)
        create_layout.addWidget(create_hint_label)
        create_layout.addWidget(self._rows_container)
        create_layout.addLayout(add_row)

        # -- "Connect Input Path" -----------------------------------------
        self._connections_container = QWidget()
        self._connections_layout = QVBoxLayout(self._connections_container)
        self._connections_layout.setContentsMargins(0, 0, 0, 0)

        connect_hint_label = QLabel("Point this repo at another repo's declared Custom Path — shown as an edge in the Graph View.")
        connect_hint_label.setWordWrap(True)
        connect_hint_label.setProperty("secondary", True)

        connect_button = QPushButton("Connect...")
        connect_button.clicked.connect(self._on_connect)

        connect_group = QGroupBox("Connect Input Path")
        connect_layout = QVBoxLayout(connect_group)
        connect_layout.addWidget(connect_hint_label)
        connect_layout.addWidget(self._connections_container)
        connect_layout.addWidget(connect_button)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(create_group)
        content_layout.addWidget(connect_group)
        content_layout.addStretch()

        scroll = wrap_scrollable(content)

        self.content_widget = QWidget()
        content_wrap_layout = QVBoxLayout(self.content_widget)
        content_wrap_layout.setContentsMargins(0, 0, 0, 0)
        content_wrap_layout.addWidget(scroll)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)

        self.refresh()

    def refresh(self) -> None:
        """Re-resolves the active project/repo from local_config_store and
        rebuilds both sections — called on construction and every time this
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
        self._rebuild_rows()
        self._connections = self.pipeline_store.get_inputs(project_id, repo_id)
        self._rebuild_connections()

    # -- "Create Input Path" ----------------------------------------------

    def _rebuild_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for index, custom_path in enumerate(self._custom_paths):
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(QLabel(f"<b>{custom_path.label}</b>"))
            path_label = QLabel(custom_path.path)
            path_label.setWordWrap(True)
            row.addWidget(path_label, stretch=1)
            rename_button = QPushButton("Rename")
            rename_button.clicked.connect(lambda _checked, i=index: self._on_rename(i))
            row.addWidget(rename_button)
            edit_path_button = QPushButton("Edit Path")
            edit_path_button.clicked.connect(lambda _checked, i=index: self._on_edit_path(i))
            row.addWidget(edit_path_button)
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda _checked, i=index: self._on_remove(i))
            row.addWidget(remove_button)
            self._rows_layout.addWidget(row_widget)

    def _on_browse_new_path(self) -> None:
        """Separate QFileDialog folder browser, rooted at the active repo's
        own folder — easier than hand-typing a relative path (confirmed
        with the user). Rejects a folder picked from outside the repo,
        since CustomPath.path is always relative to the repo's own root
        (see pipeline_store.py's CustomPath docstring); auto-fills the
        label from the folder name too if the label field is still empty."""
        if self._project_id is None or self._repo_id is None:
            return
        try:
            repo = self.store.get_repo(self._project_id, self._repo_id)
        except NotFoundError:
            return
        repo_root = Path(self.local_config_store.workspace_root) / repo.local_path
        chosen = QFileDialog.getExistingDirectory(self, "Choose Folder", str(repo_root))
        if not chosen:
            return
        chosen_path = Path(chosen)
        try:
            relative = chosen_path.relative_to(repo_root)
        except ValueError:
            QMessageBox.information(
                self,
                "Choose Folder",
                "Pick a folder inside this repo's own root — Custom Paths are always relative to it.",
            )
            return
        self.new_path_edit.setText(str(relative).replace("\\", "/"))
        if not self.new_label_edit.text().strip():
            self.new_label_edit.setText(chosen_path.name)

    def _on_add(self) -> None:
        if self._project_id is None or self._repo_id is None:
            return
        label = self.new_label_edit.text().strip()
        path = self.new_path_edit.text().strip()
        if not label or not path:
            QMessageBox.information(self, "Add Custom Path", "Enter both a label and a path.")
            return
        custom_paths = list(self._custom_paths) + [CustomPath(id=CustomPath.new_id(), label=label, path=path)]
        self._save_custom_paths(custom_paths)
        self.new_label_edit.clear()
        self.new_path_edit.clear()

    def _on_rename(self, index: int) -> None:
        if not (0 <= index < len(self._custom_paths)):
            return
        current = self._custom_paths[index]
        new_label, ok = QInputDialog.getText(self, "Rename Custom Path", "New label:", text=current.label)
        if not ok or not new_label.strip():
            return
        custom_paths = list(self._custom_paths)
        custom_paths[index] = CustomPath(id=current.id, label=new_label.strip(), path=current.path)
        self._save_custom_paths(custom_paths)

    def _on_edit_path(self, index: int) -> None:
        if not (0 <= index < len(self._custom_paths)):
            return
        current = self._custom_paths[index]
        new_path, ok = QInputDialog.getText(self, "Edit Path", "Path relative to this repo's root:", text=current.path)
        if not ok or not new_path.strip():
            return
        custom_paths = list(self._custom_paths)
        custom_paths[index] = CustomPath(id=current.id, label=current.label, path=new_path.strip())
        self._save_custom_paths(custom_paths)

    def _on_remove(self, index: int) -> None:
        if not (0 <= index < len(self._custom_paths)):
            return
        custom_paths = list(self._custom_paths)
        del custom_paths[index]
        self._save_custom_paths(custom_paths)

    def _save_custom_paths(self, custom_paths: list[CustomPath]) -> None:
        self.pipeline_store.set_custom_paths(self._project_id, self._repo_id, custom_paths)
        self._custom_paths = custom_paths
        self._rebuild_rows()

    # -- "Connect Input Path" ----------------------------------------------

    def _describe_connection(self, ref: RepoRef) -> str:
        try:
            target_name = self.store.get_repo(ref.project_id, ref.repo_id).name
        except NotFoundError:
            target_name = "(deleted repo)"
        custom_path = self.pipeline_store.get_custom_path(ref.project_id, ref.repo_id, ref.custom_path_id)
        label = custom_path.label if custom_path is not None else "(deleted custom path)"
        if ref.direction == "output":
            return f"→ {target_name} — {label} (Output)"
        return f"← {target_name} — {label} (Input)"

    def _rebuild_connections(self) -> None:
        while self._connections_layout.count():
            item = self._connections_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not self._connections:
            empty_row = QLabel("No connections yet.")
            empty_row.setProperty("secondary", True)
            self._connections_layout.addWidget(empty_row)
            return
        for index, ref in enumerate(self._connections):
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(QLabel(self._describe_connection(ref)), stretch=1)
            edit_button = QPushButton("Edit...")
            edit_button.clicked.connect(lambda _checked, i=index: self._on_edit_connection(i))
            row.addWidget(edit_button)
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda _checked, i=index: self._on_remove_connection(i))
            row.addWidget(remove_button)
            self._connections_layout.addWidget(row_widget)

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

    def _on_edit_connection(self, index: int) -> None:
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

    def _on_remove_connection(self, index: int) -> None:
        if not (0 <= index < len(self._connections)):
            return
        connections = list(self._connections)
        del connections[index]
        self._save_connections(connections)

    def _save_connections(self, connections: list[RepoRef]) -> None:
        self.pipeline_store.set_inputs(self._project_id, self._repo_id, connections)
        self._connections = connections
        self._rebuild_connections()
