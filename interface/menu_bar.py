from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QWidget

from core.version import APP_NAME, APP_VERSION
from interface.github_auth_widget import GitHubAuthWidget


class MenuBar(QWidget):
    """Top row of the main window — what used to be the bottom status bar
    (app label, sync status, Update button, GitHub login) before Settings
    stopped being a modal dialog and this whole row moved up. Not Qt's
    QMenuBar/dropdown-menu widget — just a plain widget row, since its
    contents are buttons/labels/a progress bar, not QActions."""

    login_requested = Signal()
    logout_requested = Signal()
    update_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.app_label = QLabel(f"{APP_NAME} {APP_VERSION}")
        self.status_label = QLabel("")

        self.update_button = QPushButton("Update and Restart")
        self.update_button.clicked.connect(self.update_requested.emit)
        self.update_button.setVisible(False)

        self.sync_progress_bar = QProgressBar()
        self.sync_progress_bar.setRange(0, 0)
        self.sync_progress_bar.setFixedWidth(120)
        self.sync_progress_bar.setVisible(False)

        self.github_auth_widget = GitHubAuthWidget()
        self.github_auth_widget.login_requested.connect(self.login_requested.emit)
        self.github_auth_widget.logout_requested.connect(self.logout_requested.emit)

        layout = QHBoxLayout(self)
        layout.addWidget(self.app_label)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.update_button)
        layout.addWidget(self.sync_progress_bar)
        layout.addWidget(self.github_auth_widget)

    def set_sync_message(self, text: str) -> None:
        self.status_label.setText(text)

    def set_update_available(self, available: bool) -> None:
        self.update_button.setVisible(available)
