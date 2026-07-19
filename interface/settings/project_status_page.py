from __future__ import annotations

from PySide6.QtWidgets import QAbstractItemView, QHBoxLayout, QPushButton, QTreeWidget, QVBoxLayout, QWidget

from core.store import LocalConfigStore, MetadataStore
from interface.shared.project_repo_tree import populate_project_tree


class ProjectStatusPage(QWidget):
    """Read-only view of every Project/Repo and its sync status.

    For artists to check on the registry that managers maintain in the
    Project Editor's node graph — no add/edit/delete here.
    """

    def __init__(self, parent=None, *, store: MetadataStore, local_config_store: LocalConfigStore):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Project / Repo", "Status", "Last Synced"])
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setEditTriggers(QTreeWidget.NoEditTriggers)

        self.refresh_button = QPushButton("Refresh Status")
        self.refresh_button.clicked.connect(self.refresh)

        button_row = QHBoxLayout()
        button_row.addWidget(self.refresh_button)
        button_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(button_row)
        layout.addWidget(self.tree)

        self.refresh()

    def refresh(self) -> None:
        if self.local_config_store.workspace_root:
            self.store.refresh_statuses_from_disk(self.local_config_store.workspace_root)
        populate_project_tree(self.tree, self.store)
