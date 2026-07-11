from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QThread, Signal

from core.exceptions import GitOperationError


class GitStreamWorker(QThread):
    """Runs any GitService streaming action (pull, push, ...) off the UI
    thread, generalizing the pattern GitWorker established for open_or_sync."""

    output = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, action: Callable[[Callable[[str], None]], None], parent=None):
        super().__init__(parent)
        self._action = action

    def run(self) -> None:
        try:
            self._action(self.output.emit)
            self.finished_ok.emit()
        except GitOperationError as exc:
            self.failed.emit(str(exc))
