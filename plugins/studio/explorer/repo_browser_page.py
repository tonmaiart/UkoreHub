from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.extensibility.file_opener import FileOpenerRegistry
from core.git_service import GitService
from core.models import Project, Repo
from core.os_utils import open_with_default_app
from core.paths import resolve_repo_path
from core.store import LocalConfigStore
from interface.shared.widget_helpers import show_exclusive
from plugins.studio.explorer.browser_widget import RepoBrowserWidget


class RepoBrowserPage(QWidget):
    def __init__(
        self,
        parent=None,
        *,
        local_config_store: LocalConfigStore,
        git_service: GitService,
        file_opener_registry: FileOpenerRegistry,
    ):
        super().__init__(parent)
        self.local_config_store = local_config_store
        self._file_opener_registry = file_opener_registry
        self._last_repo_id: str | None = None
        self._active_repo: Repo | None = None

        self.empty_label = QLabel("Select a repo to see this information.")
        self.not_cloned_label = QLabel("Repo not yet cloned — use Repo Git Status to sync.")
        self.browser = RepoBrowserWidget(git_service=git_service, open_file=self._open_file)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.not_cloned_label)
        layout.addWidget(self.browser)

        self.not_cloned_label.setVisible(False)
        self.browser.setVisible(False)

    def _open_file(self, path: Path) -> None:
        # Only reachable via a double-click inside Repo Browser — a file
        # opened any other way (directly launching Maya, Windows Explorer,
        # etc.) never goes through this, so a custom opener's side effects
        # (e.g. env injection) only ever apply to opens UkoreHub itself
        # triggered.
        if self._active_repo is not None:
            opener = self._file_opener_registry.find_opener(path, self._active_repo.enabled_addon_ids)
            if opener is not None and opener(path, self._active_repo):
                return
        open_with_default_app(path)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._active_repo = repo
        if repo is None:
            self._last_repo_id = None
            show_exclusive(self.empty_label, self.not_cloned_label, self.browser)
            return
        abs_path = resolve_repo_path(workspace_root, project.name, repo.name)
        if not (abs_path / ".git").exists():
            self._last_repo_id = None
            show_exclusive(self.not_cloned_label, self.empty_label, self.browser)
            return
        show_exclusive(self.browser, self.empty_label, self.not_cloned_label)
        # Only re-navigate when the repo actually changed — switching tabs
        # away and back re-invokes set_repo() with the SAME repo, and we
        # must not reset the user's current folder/selection in that case.
        if repo.id != self._last_repo_id:
            self.browser.set_root(abs_path)
            self._last_repo_id = repo.id

    def browse_to_path(self, path: Path) -> None:
        """Optional MainWindow SectionHost protocol — see
        interface/section_registry.py's SectionHost.navigate_and_focus and
        plugins/studio/submit/plugin.py's browse_file_requested wiring."""
        self.browser.browse_to_file(path)
