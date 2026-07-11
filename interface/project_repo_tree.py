from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from core.store import MetadataStore

PROJECT_ROLE = Qt.UserRole
REPO_ROLE = Qt.UserRole + 1


def populate_project_tree(tree: QTreeWidget, store: MetadataStore) -> None:
    tree.clear()
    for project in store.list_projects():
        project_item = QTreeWidgetItem([project.name, "", ""])
        project_item.setData(0, PROJECT_ROLE, project.id)
        for repo in project.repos:
            repo_item = QTreeWidgetItem([repo.name, repo.status, repo.last_synced or ""])
            repo_item.setData(0, PROJECT_ROLE, project.id)
            repo_item.setData(0, REPO_ROLE, repo.id)
            project_item.addChild(repo_item)
        tree.addTopLevelItem(project_item)
    tree.expandAll()
