from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.exceptions import GitOperationError
from core.git_service import GitService
from core.models import RepoStatus


class RepoStatusWorker(QThread):
    status_ready = Signal(object)
    failed = Signal(str)

    def __init__(self, git_service: GitService, repo_path: Path, parent=None):
        super().__init__(parent)
        self.git_service = git_service
        self.repo_path = repo_path

    def run(self) -> None:
        try:
            status: RepoStatus = self.git_service.get_status(self.repo_path)
            self.status_ready.emit(status)
        except GitOperationError as exc:
            self.failed.emit(str(exc))
