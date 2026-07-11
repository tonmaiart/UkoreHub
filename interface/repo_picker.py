from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QTreeWidget,
    QVBoxLayout,
)

from core.store import MetadataStore
from interface.project_repo_tree import PROJECT_ROLE, REPO_ROLE, populate_project_tree


class RepoPickerDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        selected_project_id: str | None = None,
        selected_repo_id: str | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Select Repo")
        self.resize(400, 400)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Project / Repo", "Status", "Last Synced"])
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        populate_project_tree(self.tree, store)
        self.tree.itemSelectionChanged.connect(self._update_ok_enabled)
        self.tree.itemDoubleClicked.connect(self._on_double_clicked)

        if selected_project_id and selected_repo_id:
            self._select_repo(selected_project_id, selected_repo_id)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        layout.addWidget(self.buttons)

        self._update_ok_enabled()

    def _select_repo(self, project_id: str, repo_id: str) -> None:
        for i in range(self.tree.topLevelItemCount()):
            project_item = self.tree.topLevelItem(i)
            if project_item.data(0, PROJECT_ROLE) != project_id:
                continue
            for j in range(project_item.childCount()):
                repo_item = project_item.child(j)
                if repo_item.data(0, REPO_ROLE) == repo_id:
                    self.tree.setCurrentItem(repo_item)
                    return

    def _update_ok_enabled(self) -> None:
        ok_button = self.buttons.button(QDialogButtonBox.Ok)
        ok_button.setEnabled(self._selected_repo_id() is not None)

    def _on_double_clicked(self, item, _column) -> None:
        if item.data(0, REPO_ROLE) is not None:
            self.accept()

    def _selected_repo_id(self) -> str | None:
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, REPO_ROLE)

    def selected_project_id(self) -> str | None:
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, PROJECT_ROLE)

    def selected_repo_id(self) -> str | None:
        return self._selected_repo_id()
