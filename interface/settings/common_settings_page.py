from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.github.auth import fetch_avatar_bytes
from core.store import LocalConfigStore

AVATAR_SIZE = 48


class _AvatarFetchWorker(QThread):
    """Downloads the signed-in user's GitHub avatar off the UI thread — same
    network-off-main-thread pattern as
    plugins/core/explorer/path_commit_history_worker.py. Needs only the
    username (fetch_avatar_bytes hits the public github.com/<user>.png
    convenience URL, no token/API call involved)."""

    avatar_ready = Signal(bytes)

    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self._username = username

    def run(self) -> None:
        avatar_bytes = fetch_avatar_bytes(self._username)
        if avatar_bytes:
            self.avatar_ready.emit(avatar_bytes)


def _format_login_at(raw: str | None) -> str:
    """Best-effort human-readable local time from the UTC ISO timestamp
    LocalConfigStore.github_login_at stores. Falls back to the raw string
    (never raises) — a display nicety isn't worth crashing Settings over."""
    if not raw:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return raw
    return dt.astimezone().strftime("%d %b %Y, %H:%M")


class CommonSettingsPage(QWidget):
    # MainWindow connects this to _on_logout_requested (also closing the
    # dialog itself, since logout closes the whole app — see that method's
    # docstring for why: login/token-caching now lives in the launcher exe,
    # not here, so "logging out" means clearing the cached token and
    # relaunching to the launcher's login screen, not just tearing down
    # some in-app gate).
    logout_requested = Signal()
    # MainWindow connects this to the same os.execv restart MainWindow's
    # own "Update and Restart" sidebar button already uses (see
    # _on_update_and_restart/_restart_app) — this one just restarts, no
    # git pull first.
    restart_requested = Signal()

    def __init__(self, parent=None, *, local_config_store: LocalConfigStore):
        super().__init__(parent)
        self._local_config_store = local_config_store
        self._avatar_worker: _AvatarFetchWorker | None = None

        username = local_config_store.github_username

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setText("\U0001F464")

        self.username_label = QLabel(username or "Not signed in")
        self.username_label.setStyleSheet("font-weight: bold;")

        self.login_at_label = QLabel(_format_login_at(local_config_store.github_login_at))
        self.login_at_label.setProperty("secondary", True)

        account_text = QVBoxLayout()
        account_text.setSpacing(2)
        account_text.addWidget(self.username_label)
        account_text.addWidget(self.login_at_label)

        account_row = QWidget()
        account_row_layout = QHBoxLayout(account_row)
        account_row_layout.setContentsMargins(0, 0, 0, 0)
        account_row_layout.addWidget(self.avatar_label)
        account_row_layout.addLayout(account_text)
        account_row_layout.addStretch()

        # Workspace folder is fixed to this install's own storage/ folder
        # (forced in launcher.py) — shown here read-only, no Browse option.
        self.workspace_label = QLabel(local_config_store.workspace_root or "")

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout_requested.emit)

        self.restart_button = QPushButton("Restart")
        self.restart_button.clicked.connect(self.restart_requested.emit)

        form = QFormLayout(self)
        form.addRow("Account:", account_row)
        form.addRow("Workspace folder:", self.workspace_label)
        form.addRow("Logout:", self.logout_button)
        form.addRow("Application:", self.restart_button)

        if username:
            self._start_avatar_fetch(username)

    def _start_avatar_fetch(self, username: str) -> None:
        self._avatar_worker = _AvatarFetchWorker(username, self)
        self._avatar_worker.avatar_ready.connect(self._on_avatar_ready)
        self._avatar_worker.start()

    def _on_avatar_ready(self, avatar_bytes: bytes) -> None:
        pixmap = QPixmap()
        pixmap.loadFromData(avatar_bytes)
        self.avatar_label.setPixmap(
            pixmap.scaled(AVATAR_SIZE, AVATAR_SIZE, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        )
