from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.exceptions import GitOperationError
from core.git_service import GitService


class GitWorker(QThread):
    output = Signal(str)
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, git_service: GitService, git_url: str, dest_path: Path, parent=None):
        super().__init__(parent)
        self.git_service = git_service
        self.git_url = git_url
        self.dest_path = dest_path

    def run(self) -> None:
        try:
            result = self.git_service.open_or_sync(
                self.git_url, self.dest_path, on_output=self.output.emit
            )
            self.finished_ok.emit(result)
        except GitOperationError as exc:
            self.failed.emit(str(exc))
        except OSError as exc:
            self.failed.emit(str(exc))
