from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import NotFoundError
from core.git_service import GitService
from core.models import Project, Repo
from core.os_utils import open_in_file_explorer
from core.paths import resolve_repo_path
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore


class RepoAboutPage(QWidget):
    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        program_store: ProgramStore,
        git_service: GitService,
    ):
        super().__init__(parent)
        self.program_store = program_store
        self._project: Project | None = None
        self._repo: Repo | None = None
        self._workspace_root: str | None = None

        self.empty_label = QLabel("Select a repo to see this information.")

        self.name_label = QLabel("—")
        self.git_url_label = QLabel("—")
        self.git_url_label.setWordWrap(True)
        self.local_path_label = QLabel("—")
        self.local_path_label.setWordWrap(True)
        self.last_synced_label = QLabel("—")
        self.status_label = QLabel("—")

        form = QFormLayout()
        form.addRow("Name:", self.name_label)
        form.addRow("Git URL:", self.git_url_label)
        form.addRow("Local Path:", self.local_path_label)
        form.addRow("Last Synced:", self.last_synced_label)
        form.addRow("Status:", self.status_label)

        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self._on_open_folder)

        self.requirements_group = QGroupBox("Requirements")
        self.requirements_list = QListWidget()
        requirements_layout = QVBoxLayout(self.requirements_group)
        requirements_layout.addWidget(self.requirements_list)

        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.addLayout(form)
        content_layout.addWidget(self.open_folder_button)
        content_layout.addWidget(self.requirements_group)
        content_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)
        self.content_widget.setVisible(False)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        self._workspace_root = workspace_root
        if repo is None:
            self.empty_label.setVisible(True)
            self.content_widget.setVisible(False)
            return
        self.empty_label.setVisible(False)
        self.content_widget.setVisible(True)
        self.name_label.setText(repo.name)
        self.git_url_label.setText(repo.git_url)
        abs_path = resolve_repo_path(workspace_root, project.name, repo.name)
        self.local_path_label.setText(str(abs_path))
        self.last_synced_label.setText(repo.last_synced or "Never")
        self.status_label.setText(repo.status)

        self.requirements_list.clear()
        for program_id in repo.required_program_ids:
            try:
                program = self.program_store.get_program(program_id)
            except NotFoundError:
                continue
            item = QListWidgetItem(program.name)
            icon_path = self.program_store.resolve_icon_path(program)
            if icon_path and icon_path.exists():
                item.setIcon(QIcon(str(icon_path)))
            self.requirements_list.addItem(item)

    def _on_open_folder(self) -> None:
        if self._repo is None:
            return
        abs_path = resolve_repo_path(self._workspace_root, self._project.name, self._repo.name)
        if not abs_path.exists():
            QMessageBox.information(self, "Open Folder", "This repo has not been cloned yet.")
            return
        if not open_in_file_explorer(abs_path):
            QMessageBox.warning(self, "Open Folder", "Could not open the file explorer.")
