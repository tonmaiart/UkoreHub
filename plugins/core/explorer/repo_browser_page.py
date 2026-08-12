from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.extensibility.file_opener import FileOpenerRegistry
from core.vcs.git_service import GitService
from core.models import Project, Repo
from core.os_utils import open_with_default_app
from core.storage.config_store import LocalConfigStore
from interface.shared.widget_helpers import show_exclusive
from plugins.core.explorer.browser_widget import RepoBrowserWidget


class RepoBrowserPage(QWidget):
    def __init__(
        self,
        parent=None,
        *,
        local_config_store: LocalConfigStore,
        git_service: GitService,
        file_opener_registry: FileOpenerRegistry,
        cache_dir: Path,
        api=None,
    ):
        super().__init__(parent)
        self.local_config_store = local_config_store
        self._file_opener_registry = file_opener_registry
        self._last_repo_id: str | None = None
        self._active_repo: Repo | None = None
        self._api = api

        self.empty_label = QLabel("Select a repo to see this information.")
        self.not_cloned_label = QLabel("Repo not yet cloned — use Repo Git Status to sync.")

        self.browser = RepoBrowserWidget(
            git_service=git_service,
            open_file=self._open_file,
            cache_dir=cache_dir,
            debug_bus=api.debug_bus if api else None,
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.not_cloned_label)
        layout.addWidget(self.browser)

        self.not_cloned_label.setVisible(False)
        self.browser.setVisible(False)

    def _open_file(self, path: Path) -> None:
        if self._active_repo is not None:
            opener = self._file_opener_registry.find_opener(path)
            if opener is not None and opener(path, self._active_repo):
                return
        open_with_default_app(path)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._active_repo = repo
        if repo is None or not workspace_root:
            self._last_repo_id = None
            show_exclusive(self.empty_label, self.not_cloned_label, self.browser)
            return

        abs_path = (Path(workspace_root) / repo.local_path).resolve()

        if self._api and self._api.debug_bus:
            self._api.debug_bus.log("Explorer", f"set_repo: {repo.name} -> {abs_path}")

        if not abs_path.exists() or not (abs_path / ".git").exists():
            if self._api and self._api.debug_bus:
                self._api.debug_bus.log("Explorer", f"[WARN] Repo not cloned or missing .git at {abs_path}")
            self._last_repo_id = None
            show_exclusive(self.not_cloned_label, self.empty_label, self.browser)
            return

        show_exclusive(self.browser, self.empty_label, self.not_cloned_label)
        if repo.id != self._last_repo_id:
            self.browser.set_root(abs_path, repo_id=repo.id)
            self._last_repo_id = repo.id

    def browse_to_path(self, path: Path) -> None:
        self.browser.browse_to_file(path)