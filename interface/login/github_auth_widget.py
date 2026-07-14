from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from interface.login.github_avatar_worker import GitHubAvatarWorker
from interface.sidebar.circular_pixmap import circular_pixmap

AVATAR_SIZE = 24


class GitHubAuthWidget(QWidget):
    """Avatar + username display, plus (optionally) the Login/Logout toggle
    button. `launch_dialog.py`'s mandatory login gate needs the toggle (the
    user isn't logged in yet there); Sidebar's footer sets
    show_toggle_button=False since logout now lives as its own button in
    Settings > Common instead — Sidebar only ever shows a logged-in user, so
    the toggle would always read "Logout" there anyway."""

    login_requested = Signal()
    logout_requested = Signal()

    def __init__(self, parent=None, *, show_toggle_button: bool = True):
        super().__init__(parent)
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        self.username_label = QLabel("Not logged in")
        self.toggle_button = QPushButton("Login")
        self.toggle_button.clicked.connect(self._on_toggle_clicked)
        self.toggle_button.setVisible(show_toggle_button)
        self._logged_in = False
        self._avatar_worker: GitHubAvatarWorker | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.avatar_label)
        layout.addWidget(self.username_label)
        layout.addWidget(self.toggle_button)

    def set_state(self, username: str | None) -> None:
        self._logged_in = username is not None
        self.username_label.setText(username if username else "Not logged in")
        self.toggle_button.setText("Logout" if self._logged_in else "Login")
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

    def _on_toggle_clicked(self) -> None:
        if self._logged_in:
            self.logout_requested.emit()
        else:
            self.login_requested.emit()
