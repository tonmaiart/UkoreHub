from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from core.models import Repo
from core.store import MetadataStore

PROJECT_ROLE = Qt.UserRole
REPO_ROLE = Qt.UserRole + 1


def _default_repo_columns(repo: Repo) -> list[str]:
    return [repo.status, repo.last_synced or ""]


def populate_project_tree(
    tree: QTreeWidget,
    store: MetadataStore,
    *,
    repo_extra_columns: Callable[[Repo], list[str]] = _default_repo_columns,
) -> None:
    """Fills `tree` with Project/Repo rows. `tree`'s header (set by the
    caller via setHeaderLabels before calling this) determines how many
    extra columns beyond the name are shown; repo_extra_columns must return
    that many values. Defaults to Status/Last Synced (ProjectStatusPage,
    RepoPickerDialog); plugins/studio/project_editor's graph view resolves
    repos directly rather than via this tree, but reuses the same
    MetadataStore.list_projects() ordering."""
    tree.clear()
    blank_columns = [""] * (tree.columnCount() - 1)
    for project in store.list_projects():
        project_item = QTreeWidgetItem([project.name, *blank_columns])
        project_item.setData(0, PROJECT_ROLE, project.id)
        for repo in project.repos:
            repo_item = QTreeWidgetItem([repo.name, *repo_extra_columns(repo)])
            repo_item.setData(0, PROJECT_ROLE, project.id)
            repo_item.setData(0, REPO_ROLE, repo.id)
            project_item.addChild(repo_item)
        tree.addTopLevelItem(project_item)
    tree.expandAll()
