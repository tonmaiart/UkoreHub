from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from plugin_api import FileChange, GitOperationError, GitService


class FileLocalChangeWorker(QThread):
    """Looks up whether relative_path has an uncommitted local change
    (working tree modification/untracked/staged), off the UI thread —
    GitService.get_status(repo_path) runs `git status --porcelain` which,
    like the commit-history fetch, is too slow to call synchronously from
    _on_table_selection_changed."""

    result_ready = Signal(object)  # tuple[FileChange | None, datetime | None]

    def __init__(self, git_service: GitService, repo_path: Path, relative_path: str, parent=None):
        super().__init__(parent)
        self.git_service = git_service
        self.repo_path = repo_path
        self.relative_path = relative_path

    def run(self) -> None:
        change: FileChange | None = None
        try:
            status = self.git_service.get_status(self.repo_path)
            for file_change in (*status.unstaged_changes, *status.staged_changes):
                if file_change.path == self.relative_path:
                    change = file_change
                    break
        except GitOperationError:
            change = None

        mtime: datetime | None = None
        if change is not None:
            try:
                mtime = datetime.fromtimestamp((self.repo_path / self.relative_path).stat().st_mtime)
            except OSError:
                mtime = None

        self.result_ready.emit((change, mtime))
