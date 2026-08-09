from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.exceptions import GitOperationError
from core.vcs.git_service import GitService
from core.models import Repo


class RequiredRepoCloneWorker(QThread):
    """Clones/pulls a fixed list of repos required by pipeline_inputs
    connections, sequentially, off the UI thread. A local duplicate of
    submit/git_stream_worker.py's "QThread wraps a callable" shape rather
    than an import of it — project_editor must not reach into a sibling
    plugin's source, see CLAUDE.md. Stops at the first failure, leaving any
    repos already cloned earlier in this batch on disk (never rolled back)."""

    repo_progress = Signal(str)
    finished_ok = Signal()
    failed = Signal(str, str)

    def __init__(self, *, git_service: GitService, workspace_root: str, targets: list[tuple[str, Repo]], parent=None):
        super().__init__(parent)
        self._git_service = git_service
        self._workspace_root = workspace_root
        self._targets = targets

    def run(self) -> None:
        for _project_id, repo in self._targets:
            self.repo_progress.emit(repo.name)
            dest = Path(self._workspace_root) / repo.local_path
            try:
                self._git_service.open_or_sync(repo.git_url, dest)
            except (GitOperationError, OSError) as exc:
                self.failed.emit(repo.name, str(exc))
                return
        self.finished_ok.emit()
