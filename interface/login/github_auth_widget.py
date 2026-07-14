from __future__ import annotations

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from interface.login.github_avatar_worker import GitHubAvatarWorker
from interface.sidebar.circular_pixmap import circular_pixmap

AVATAR_SIZE = 24


class GitHubAuthWidget(QWidget):
    """Avatar + username display for Sidebar's footer — Sidebar only ever
    shows a logged-in user (the mandatory login gate is `login_overlay.py`'s
    LoginOverlay, and logout lives as its own button in Settings > Common),
    so this widget is display-only with no login/logout control of its
    own."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        self.username_label = QLabel("Not logged in")
        self._avatar_worker: GitHubAvatarWorker | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.avatar_label)
        layout.addWidget(self.username_label)

    def set_state(self, username: str | None) -> None:
        self.username_label.setText(username if username else "Not logged in")
        if username:
            self._fetch_avatar(username)
        else:
            self.avatar_label.clear()

    def _fetch_avatar(self, username: str) -> None:
        self._avatar_worker = GitHubAvatarWorker(username)
        self._avatar_worker.avatar_ready.connect(self._on_avatar_ready)
        self._avatar_worker.start()

    def _on_avatar_ready(self, avatar_bytes) -> None:
        if not avatar_bytes:
            return
        pixmap = QPixmap()
        pixmap.loadFromData(avatar_bytes)
        self.avatar_label.setPixmap(circular_pixmap(pixmap, AVATAR_SIZE))
