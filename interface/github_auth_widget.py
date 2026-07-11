from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class GitHubAuthWidget(QWidget):
    login_requested = Signal()
    logout_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.username_label = QLabel("Not logged in")
        self.toggle_button = QPushButton("Login")
        self.toggle_button.clicked.connect(self._on_toggle_clicked)
        self._logged_in = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.username_label)
        layout.addWidget(self.toggle_button)

    def set_state(self, username: str | None) -> None:
        self._logged_in = username is not None
        self.username_label.setText(username if username else "Not logged in")
        self.toggle_button.setText("Logout" if self._logged_in else "Login")

    def _on_toggle_clicked(self) -> None:
        if self._logged_in:
            self.logout_requested.emit()
        else:
            self.login_requested.emit()
