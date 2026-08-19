from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from plugin_api import GitOperationError, GitService


class RepoStatusScanWorker(QThread):
    """Background working-tree status check for every currently-cloned repo
    in the table (tableWidget_Repo's Status column) — a local duplicate of
    submit/git_stream_worker.py's QThread-wraps-a-callable shape rather than
    an import of it, same boundary rule required_repo_clone_worker.py
    already follows in this plugin. Unlike that worker, this one does NOT
    stop at the first failure — one repo's git status has no bearing on any
    other row, so every target is still checked."""

    status_ready = Signal(str, bool)  # repo_id, is_dirty
    status_failed = Signal(str)  # repo_id
    scan_finished = Signal()

    def __init__(self, *, git_service: GitService, targets: list[tuple[str, Path]], parent=None):
        super().__init__(parent)
        self._git_service = git_service
        self._targets = targets

    def run(self) -> None:
        for repo_id, repo_path in self._targets:
            try:
                status = self._git_service.get_status(repo_path)
            except (GitOperationError, OSError):
                self.status_failed.emit(repo_id)
                continue
            is_dirty = bool(status.unstaged_changes or status.staged_changes)
            self.status_ready.emit(repo_id, is_dirty)
        self.scan_finished.emit()
