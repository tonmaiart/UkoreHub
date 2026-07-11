from __future__ import annotations

import shutil

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import UkoreHubError
from core.store import LocalConfigStore, MetadataStore
from interface.dialogs import ProjectDialog, RepoDialog
from interface.project_repo_tree import PROJECT_ROLE, REPO_ROLE, populate_project_tree


class ProjectDataEditorPage(QWidget):
    def __init__(self, parent=None, *, store: MetadataStore, local_config_store: LocalConfigStore):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Project / Repo", "Status", "Last Synced"])
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
        populate_project_tree(self.tree, self.store)

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
        dialog = RepoDialog(self)
        if dialog.exec():
            try:
                repo = self.store.add_repo(project_id, dialog.name(), dialog.git_url(), workspace_root)
            except UkoreHubError as exc:
                QMessageBox.warning(self, "Add Repo", str(exc))
                return
            if dialog.chosen_thumbnail_path():
                self._save_thumbnail(project_id, repo.id, dialog.chosen_thumbnail_path())
            self.refresh_tree()

    def _on_edit(self) -> None:
        project_id = self._selected_project_id()
        repo_id = self._selected_repo_id()
        if not project_id:
            QMessageBox.information(self, "Edit", "Select a project or repo first.")
            return
        if repo_id:
            repo = self.store.get_repo(project_id, repo_id)
            dialog = RepoDialog(
                self, name=repo.name, git_url=repo.git_url, thumbnail_path=self.store.resolve_thumbnail_path(repo)
            )
            if dialog.exec():
                try:
                    self.store.edit_repo(project_id, repo_id, name=dialog.name(), git_url=dialog.git_url())
                except UkoreHubError as exc:
                    QMessageBox.warning(self, "Edit Repo", str(exc))
                    return
                if dialog.chosen_thumbnail_path():
                    self._save_thumbnail(project_id, repo_id, dialog.chosen_thumbnail_path())
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
            confirm = QMessageBox.warning(
                self,
                "Delete Repo",
                f"Delete repo '{repo.name}' from the registry for EVERYONE at the studio?\n\n"
                "This removes it from the shared registry immediately and cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                self.store.delete_repo(project_id, repo_id)
                self.refresh_tree()
        else:
            project = self.store.get_project(project_id)
            confirm = QMessageBox.warning(
                self,
                "Delete Project",
                f"Delete project '{project.name}' and ALL its repos from the registry for EVERYONE at the studio?\n\n"
                "This removes them from the shared registry immediately and cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                self.store.delete_project(project_id)
                self.refresh_tree()

    def _save_thumbnail(self, project_id: str, repo_id: str, source_path) -> None:
        thumbnails_dir = self.store.thumbnails_dir
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        ext = source_path.suffix or ".png"
        dest_path = thumbnails_dir / f"{repo_id}{ext}"
        try:
            shutil.copyfile(source_path, dest_path)
        except OSError as exc:
            QMessageBox.warning(self, "Thumbnail", f"Could not save thumbnail: {exc}")
            return
        self.store.set_repo_thumbnail(project_id, repo_id, dest_path.name)
