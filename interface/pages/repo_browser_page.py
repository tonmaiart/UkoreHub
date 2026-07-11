from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.git_service import GitService
from core.models import Project, Repo
from core.paths import resolve_repo_path
from core.store import LocalConfigStore, MetadataStore
from interface.repo_browser.browser_widget import RepoBrowserWidget


class RepoBrowserPage(QWidget):
    def __init__(self, parent=None, *, store: MetadataStore, local_config_store: LocalConfigStore, git_service: GitService):
        super().__init__(parent)

        self.empty_label = QLabel("Select a repo to see this information.")
        self.not_cloned_label = QLabel("Repo not yet cloned — use Repo Git Status to sync.")
        self.browser = RepoBrowserWidget()

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.not_cloned_label)
        layout.addWidget(self.browser)

        self.not_cloned_label.setVisible(False)
        self.browser.setVisible(False)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        if repo is None:
            self.empty_label.setVisible(True)
            self.not_cloned_label.setVisible(False)
            self.browser.setVisible(False)
            return
        abs_path = resolve_repo_path(workspace_root, project.name, repo.name)
        if not (abs_path / ".git").exists():
            self.empty_label.setVisible(False)
            self.not_cloned_label.setVisible(True)
            self.browser.setVisible(False)
            return
        self.empty_label.setVisible(False)
        self.not_cloned_label.setVisible(False)
        self.browser.setVisible(True)
        self.browser.set_root(abs_path)
