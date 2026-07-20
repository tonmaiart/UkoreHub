from __future__ import annotations

import os
import sys

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox, QPushButton

from core import self_update
from core.exceptions import UkoreHubError
from core.extensibility.hooks import GitHookContext, GitHookEvent
from interface.sidebar_footer_action_registry import SidebarFooterActionSpec

FOOTER_ACTION_KEY = "self_update"


class _UpdateCheckWorker(QThread):
    update_available = Signal(bool)

    def run(self) -> None:
        try:
            available = self_update.check_for_update()
        except UkoreHubError:
            available = False
        self.update_available.emit(available)


def register(api) -> None:
    button = QPushButton("Update and Restart")
    button.setVisible(False)

    # Populated by _on_app_started — closeEvent's background_threads sweep
    # reads this list to terminate any still-running check on shutdown.
    workers: list[_UpdateCheckWorker] = []

    def _on_clicked() -> None:
        try:
            self_update.pull_update()
        except UkoreHubError as exc:
            QMessageBox.warning(button, "Update Failed", str(exc))
            return
        # Same restart mechanism as interface/main_window.py's
        # _restart_app — duplicated here since that's a MainWindow-private
        # staticmethod this plugin has no reference to.
        os.execv(sys.executable, [sys.executable, *sys.argv])

    button.clicked.connect(_on_clicked)

    def _on_app_started(context: GitHookContext) -> None:
        worker = _UpdateCheckWorker()
        worker.update_available.connect(button.setVisible)
        workers.append(worker)
        worker.start()

    api.register_sidebar_footer_action(
        SidebarFooterActionSpec(
            key=FOOTER_ACTION_KEY,
            order=10,
            widget_factory=lambda: button,
            background_threads=lambda _widget: list(workers),
        )
    )
    api.register_git_hook(GitHookEvent.APP_STARTED, _on_app_started)
