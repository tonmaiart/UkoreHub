from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.git_service import GitService


class CommitLogWorker(QThread):
    log_ready = Signal(list)

    def __init__(self, git_service: GitService, repo_path: Path, skip: int, limit: int, parent=None):
        super().__init__(parent)
        self.git_service = git_service
        self.repo_path = repo_path
        self.skip = skip
        self.limit = limit

    def run(self) -> None:
        commits = self.git_service.get_commit_log(self.repo_path, skip=self.skip, limit=self.limit)
        self.log_ready.emit(commits)
