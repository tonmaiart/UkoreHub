from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QThread, Signal

from core.exceptions import GitOperationError


class GitStreamWorker(QThread):
    """Runs any GitService streaming action (pull, push, open_or_sync, ...)
    off the UI thread. `action` is called with an on_output callback and
    may return a result (e.g. open_or_sync's "cloned"/"pulled" status
    string) — finished_ok carries whatever it returns, or None for actions
    like pull/push that don't return anything. This used to be two
    separate classes (this one for pull/push, GitWorker for open_or_sync
    specifically) that differed only in whether finished_ok carried a
    value — one generic worker covers both."""

    output = Signal(str)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, action: Callable[[Callable[[str], None]], object], parent=None):
        super().__init__(parent)
        self._action = action

    def run(self) -> None:
        try:
            result = self._action(self.output.emit)
            self.finished_ok.emit(result)
        except (GitOperationError, OSError) as exc:
            self.failed.emit(str(exc))
