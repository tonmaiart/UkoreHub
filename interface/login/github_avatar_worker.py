from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core.github.auth import fetch_avatar_bytes


class GitHubAvatarWorker(QThread):
    avatar_ready = Signal(object)

    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.username = username

    def run(self) -> None:
        self.avatar_ready.emit(fetch_avatar_bytes(self.username))
