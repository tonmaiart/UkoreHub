from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from core.git_service import GitService
from core.models import Project, Repo
from core.store import LocalConfigStore, MetadataStore


class ProjectInfoPage(QWidget):
    def __init__(self, parent=None, *, store: MetadataStore, local_config_store: LocalConfigStore, git_service: GitService):
        super().__init__(parent)
        self.store = store

        self.title_label = QLabel("Select a repo to see this information.")
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Status", "Last Synced"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.table)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        if project is None:
            self.title_label.setText("Select a repo to see this information.")
            self.table.setRowCount(0)
            return
        self.title_label.setText(f"Project: {project.name}")
        self.table.setRowCount(len(project.repos))
        for row, project_repo in enumerate(project.repos):
            self.table.setItem(row, 0, QTableWidgetItem(project_repo.name))
            self.table.setItem(row, 1, QTableWidgetItem(project_repo.status))
            self.table.setItem(row, 2, QTableWidgetItem(project_repo.last_synced or ""))
