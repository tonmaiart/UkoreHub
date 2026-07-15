from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from core.addon_store import AddonMetadataStore
from core.exceptions import NotFoundError, UkoreHubError
from core.extensibility.loader import DiscoveredPlugin
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore
from interface.login.repo_picker import RepoPickerDialog
from interface.shared.dialogs import ProjectDialog, RepoDialog
from interface.shared.image_asset import save_image_asset
from interface.shared.project_repo_tree import PROJECT_ROLE, REPO_ROLE, populate_project_tree
from interface.shared.widget_helpers import confirm_action
from plugins.studio.pipeline_architect.pipeline_store import PipelineStore, RepoRef


class ProjectDataEditorPage(QWidget):
    """CRUD for the whole Project/Repo registry — moved here verbatim from
    the former built-in interface/settings/project_data_editor_page.py (see
    plugins/studio/pipeline_architect/README.md for why), plus a "Pipeline"
    panel (added by this plugin) letting the same admin declare which repos
    feed into / out of whichever repo is selected in the tree — see
    pipeline_store.py for the storage shape."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        program_store: ProgramStore,
        addon_store: AddonMetadataStore,
        addon_catalog: list[DiscoveredPlugin],
        pipeline_store: PipelineStore,
    ):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self.program_store = program_store
        self.addon_store = addon_store
        self.addon_catalog = addon_catalog
        self.pipeline_store = pipeline_store
        self._pipeline_repo: tuple[str, str] | None = None

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Project / Repo", "Repo URL"])
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)

        add_project_btn = QPushButton("Add Project")
        add_repo_btn = QPushButton("Add Repo")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        add_project_btn.clicked.connect(self._on_add_project)
        add_repo_btn.clicked.connect(self._on_add_repo)
        edit_btn.clicked.connect(self._on_edit)
        delete_btn.clicked.connect(self._on_delete)

        button_row = QHBoxLayout()
        for button in (add_project_btn, add_repo_btn, edit_btn, delete_btn):
            button_row.addWidget(button)
        button_row.addStretch()

        self.pipeline_group = QGroupBox("Pipeline")
        self.inputs_list = QListWidget()
        self.inputs_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.outputs_list = QListWidget()
        self.outputs_list.setSelectionMode(QAbstractItemView.SingleSelection)
        add_input_btn = QPushButton("Add Input Repo...")
        add_input_btn.clicked.connect(self._on_add_input)
        remove_input_btn = QPushButton("Remove Selected")
        remove_input_btn.clicked.connect(self._on_remove_input)
        add_output_btn = QPushButton("Add Output Repo...")
        add_output_btn.clicked.connect(self._on_add_output)
        remove_output_btn = QPushButton("Remove Selected")
        remove_output_btn.clicked.connect(self._on_remove_output)

        inputs_column = QVBoxLayout()
        inputs_column.addWidget(QLabel("Inputs (repos that feed into this one)"))
        inputs_column.addWidget(self.inputs_list)
        inputs_button_row = QHBoxLayout()
        inputs_button_row.addWidget(add_input_btn)
        inputs_button_row.addWidget(remove_input_btn)
        inputs_column.addLayout(inputs_button_row)

        outputs_column = QVBoxLayout()
        outputs_column.addWidget(QLabel("Outputs (repos this one feeds into)"))
        outputs_column.addWidget(self.outputs_list)
        outputs_button_row = QHBoxLayout()
        outputs_button_row.addWidget(add_output_btn)
        outputs_button_row.addWidget(remove_output_btn)
        outputs_column.addLayout(outputs_button_row)

        pipeline_layout = QHBoxLayout(self.pipeline_group)
        pipeline_layout.addLayout(inputs_column)
        pipeline_layout.addLayout(outputs_column)
        self.pipeline_group.setVisible(False)

        layout = QVBoxLayout(self)
        layout.addLayout(button_row)
        layout.addWidget(self.tree)
        layout.addWidget(self.pipeline_group)

        self.refresh_tree()

    # -- Project/Repo CRUD (unchanged from the former built-in page) -------

    def refresh_tree(self) -> None:
        populate_project_tree(self.tree, self.store, repo_extra_columns=lambda repo: [repo.git_url])

    def _selected_project_id(self) -> str | None:
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, PROJECT_ROLE)

    def _selected_repo_id(self) -> str | None:
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, REPO_ROLE)

    def _on_add_project(self) -> None:
        dialog = ProjectDialog(self)
        if dialog.exec():
            try:
                self.store.add_project(dialog.name())
            except UkoreHubError as exc:
                QMessageBox.warning(self, "Add Project", str(exc))
                return
            self.refresh_tree()

    def _on_add_repo(self) -> None:
        project_id = self._selected_project_id()
        if not project_id:
            QMessageBox.information(self, "Add Repo", "Select a project first.")
            return
        workspace_root = self.local_config_store.workspace_root
        if not workspace_root:
            QMessageBox.information(
                self, "Add Repo", "Set and save a workspace folder in the Common tab first."
            )
            return
        dialog = RepoDialog(
            self, program_store=self.program_store, addon_catalog=self.addon_catalog, addon_store=self.addon_store
        )
        if dialog.exec():
            try:
                repo = self.store.add_repo(project_id, dialog.name(), dialog.git_url(), workspace_root)
            except UkoreHubError as exc:
                QMessageBox.warning(self, "Add Repo", str(exc))
                return
            if dialog.chosen_thumbnail_path():
                self._save_thumbnail(project_id, repo.id, dialog.chosen_thumbnail_path())
            self.store.set_repo_requirements(project_id, repo.id, dialog.selected_program_ids())
            self.store.set_repo_enabled_addons(project_id, repo.id, dialog.selected_addon_ids())
            self.refresh_tree()

    def _on_edit(self) -> None:
        project_id = self._selected_project_id()
        repo_id = self._selected_repo_id()
        if not project_id:
            QMessageBox.information(self, "Edit", "Select a project or repo first.")
            return
        if repo_id:
            repo = self.store.get_repo(project_id, repo_id)
            # Thumbnail and Requirements/Add-ons are edited from About >
            # About and About > Requirement now — only Name/Git URL stay
            # editable here (see RepoDialog's show_thumbnail docstring).
            dialog = RepoDialog(self, name=repo.name, git_url=repo.git_url, show_thumbnail=False)
            if dialog.exec():
                try:
                    self.store.edit_repo(project_id, repo_id, name=dialog.name(), git_url=dialog.git_url())
                except UkoreHubError as exc:
                    QMessageBox.warning(self, "Edit Repo", str(exc))
                    return
                self.refresh_tree()
        else:
            project = self.store.get_project(project_id)
            dialog = ProjectDialog(self, name=project.name)
            if dialog.exec():
                try:
                    self.store.rename_project(project_id, dialog.name())
                except UkoreHubError as exc:
                    QMessageBox.warning(self, "Edit Project", str(exc))
                    return
                self.refresh_tree()

    def _on_delete(self) -> None:
        project_id = self._selected_project_id()
        repo_id = self._selected_repo_id()
        if not project_id:
            QMessageBox.information(self, "Delete", "Select a project or repo first.")
            return
        if repo_id:
            repo = self.store.get_repo(project_id, repo_id)
            confirmed = confirm_action(
                self,
                "Delete Repo",
                f"Delete repo '{repo.name}' from the registry for EVERYONE at the studio?\n\n"
                "This removes it from the shared registry immediately and cannot be undone.",
            )
            if confirmed:
                self.store.delete_repo(project_id, repo_id)
                self.refresh_tree()
        else:
            project = self.store.get_project(project_id)
            confirmed = confirm_action(
                self,
                "Delete Project",
                f"Delete project '{project.name}' and ALL its repos from the registry for EVERYONE at the studio?\n\n"
                "This removes them from the shared registry immediately and cannot be undone.",
            )
            if confirmed:
                self.store.delete_project(project_id)
                self.refresh_tree()

    def _save_thumbnail(self, project_id: str, repo_id: str, source_path) -> None:
        filename = save_image_asset(
            self, source_path=source_path, dest_dir=self.store.thumbnails_dir, asset_id=repo_id
        )
        if filename is not None:
            self.store.set_repo_thumbnail(project_id, repo_id, filename)

    # -- Pipeline inputs/outputs (this plugin's own addition) --------------

    def _on_tree_selection_changed(self) -> None:
        project_id = self._selected_project_id()
        repo_id = self._selected_repo_id()
        self._pipeline_repo = (project_id, repo_id) if project_id and repo_id else None
        self.pipeline_group.setVisible(self._pipeline_repo is not None)
        if self._pipeline_repo is not None:
            self._refresh_pipeline_lists()

    def _resolve_ref_label(self, ref: RepoRef) -> str:
        try:
            project = self.store.get_project(ref.project_id)
            repo = self.store.get_repo(ref.project_id, ref.repo_id)
        except NotFoundError:
            return "(deleted repo)"
        return f"{project.name} / {repo.name}"

    def _refresh_pipeline_lists(self) -> None:
        if self._pipeline_repo is None:
            return
        project_id, repo_id = self._pipeline_repo
        self.inputs_list.clear()
        for ref in self.pipeline_store.get_inputs(project_id, repo_id):
            item = QListWidgetItem(self._resolve_ref_label(ref))
            item.setData(Qt.UserRole, ref)
            self.inputs_list.addItem(item)
        self.outputs_list.clear()
        for ref in self.pipeline_store.get_outputs(project_id, repo_id):
            item = QListWidgetItem(self._resolve_ref_label(ref))
            item.setData(Qt.UserRole, ref)
            self.outputs_list.addItem(item)

    def _pick_repo_ref(self) -> RepoRef | None:
        dialog = RepoPickerDialog(self, store=self.store)
        if not dialog.exec():
            return None
        target_project_id = dialog.selected_project_id()
        target_repo_id = dialog.selected_repo_id()
        if not target_project_id or not target_repo_id:
            return None
        return RepoRef(project_id=target_project_id, repo_id=target_repo_id)

    def _on_add_input(self) -> None:
        self._add_pipeline_ref(self.pipeline_store.get_inputs, self.pipeline_store.set_inputs)

    def _on_add_output(self) -> None:
        self._add_pipeline_ref(self.pipeline_store.get_outputs, self.pipeline_store.set_outputs)

    def _add_pipeline_ref(self, get_refs, set_refs) -> None:
        if self._pipeline_repo is None:
            return
        project_id, repo_id = self._pipeline_repo
        ref = self._pick_repo_ref()
        if ref is None:
            return
        if ref.project_id == project_id and ref.repo_id == repo_id:
            return  # a repo can't be its own pipeline input/output
        refs = get_refs(project_id, repo_id)
        if any(r.project_id == ref.project_id and r.repo_id == ref.repo_id for r in refs):
            return  # already listed
        refs.append(ref)
        set_refs(project_id, repo_id, refs)
        self._refresh_pipeline_lists()

    def _on_remove_input(self) -> None:
        self._remove_pipeline_ref(self.inputs_list, self.pipeline_store.get_inputs, self.pipeline_store.set_inputs)

    def _on_remove_output(self) -> None:
        self._remove_pipeline_ref(self.outputs_list, self.pipeline_store.get_outputs, self.pipeline_store.set_outputs)

    def _remove_pipeline_ref(self, list_widget: QListWidget, get_refs, set_refs) -> None:
        if self._pipeline_repo is None:
            return
        items = list_widget.selectedItems()
        if not items:
            return
        removed: RepoRef = items[0].data(Qt.UserRole)
        project_id, repo_id = self._pipeline_repo
        refs = [r for r in get_refs(project_id, repo_id) if not (r.project_id == removed.project_id and r.repo_id == removed.repo_id)]
        set_refs(project_id, repo_id, refs)
        self._refresh_pipeline_lists()
