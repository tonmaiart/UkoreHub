from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from plugin_api import (
    FileOpenerRegistry,
    GitService,
    LocalConfigStore,
    Project,
    Repo,
    open_with_default_app,
    show_exclusive,
)
from plugins.core.explorer.browser_widget import RepoBrowserWidget

logger = logging.getLogger("Explorer")


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
        self._active_project_id: str | None = None
        self._workspace_root: str | None = None
        self._api = api

        self.empty_label = QLabel("Select a repo to see this information.")
        self.not_cloned_label = QLabel("Repo not yet cloned — use Repo Git Status to sync.")

        self.browser = RepoBrowserWidget(
            git_service=git_service,
            open_file=self._open_file,
            cache_dir=cache_dir,
            metadata_store=api.metadata if api else None,
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
        self._workspace_root = workspace_root
        if project is not None:
            self._active_project_id = project.id
        if repo is None or not workspace_root:
            self._last_repo_id = None
            show_exclusive(self.empty_label, self.not_cloned_label, self.browser)
            return

        abs_path = (Path(workspace_root) / repo.local_path).resolve()

        logger.info(f"set_repo: {repo.name} -> {abs_path}")

        if not abs_path.exists() or not (abs_path / ".git").exists():
            logger.warning(f"Repo not cloned or missing .git at {abs_path}")
            self._last_repo_id = None
            show_exclusive(self.not_cloned_label, self.empty_label, self.browser)
            return

        show_exclusive(self.browser, self.empty_label, self.not_cloned_label)
        if repo.id != self._last_repo_id:
            self.browser.set_root(abs_path, repo_id=repo.id, project_id=self._active_project_id)
            self._last_repo_id = repo.id

    def browse_to_path(self, path: Path) -> None:
        self.browser.browse_to_file(path)

    def refresh_content(self) -> None:
        """RefreshablePage protocol (interface/page_protocols.py) — called
        via UICommandService.refresh_section when another section (Submit,
        after a sync) knows the working tree changed underneath this page.
        Re-runs the same not-cloned/exists check set_repo does, covering
        "just cloned for the first time" (set_root has never run yet); if
        this page was already showing the same repo, set_repo's
        repo.id == _last_repo_id guard would skip re-scanning, so force one
        via browser.reload() instead (covers "pulled more commits into an
        already-cloned repo")."""
        if self._active_repo is None or not self._workspace_root:
            return
        if self._active_repo.id == self._last_repo_id:
            self.browser.reload()
        else:
            self.set_repo(None, self._active_repo, self._workspace_root)