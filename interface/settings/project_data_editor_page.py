from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from core.addon_store import AddonMetadataStore
from core.exceptions import UkoreHubError
from core.extensibility.loader import DiscoveredPlugin
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore
from interface.shared.dialogs import ProjectDialog, RepoDialog
from interface.shared.image_asset import save_image_asset
from interface.shared.project_repo_tree import PROJECT_ROLE, REPO_ROLE, populate_project_tree
from interface.shared.widget_helpers import confirm_action


class ProjectDataEditorPage(QWidget):
    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        program_store: ProgramStore,
        addon_store: AddonMetadataStore,
        addon_catalog: list[DiscoveredPlugin],
    ):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self.program_store = program_store
        self.addon_store = addon_store
        self.addon_catalog = addon_catalog

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Project / Repo", "Repo URL"])
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)

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

        layout = QVBoxLayout(self)
        layout.addLayout(button_row)
        layout.addWidget(self.tree)

        self.refresh_tree()

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
