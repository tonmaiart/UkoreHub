from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from interface.github_auth_worker import GitHubAuthWorker


class GitHubLoginDialog(QDialog):
    def __init__(self, parent=None, *, client_id: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("GitHub Login")
        self.resize(400, 220)
        self.username: str | None = None
        self.token: str | None = None

        self.instructions_label = QLabel("Starting GitHub login...")
        self.instructions_label.setWordWrap(True)
        self.code_label = QLabel("")
        self.code_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.copy_button = QPushButton("Copy Code")
        self.copy_button.clicked.connect(self._copy_code)
        self.copy_button.setEnabled(False)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        buttons.rejected.connect(self._on_cancel)

        layout = QVBoxLayout(self)
        layout.addWidget(self.instructions_label)
        layout.addWidget(self.code_label)
        layout.addWidget(self.copy_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(buttons)

        self.worker = GitHubAuthWorker(client_id)
        self.worker.code_ready.connect(self._on_code_ready)
        self.worker.authenticated.connect(self._on_authenticated)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_code_ready(self, user_code: str, verification_uri: str) -> None:
        self.instructions_label.setText(
            f"Your browser should have opened to {verification_uri} — enter this code there:"
        )
        self.code_label.setText(user_code)
        self.copy_button.setEnabled(True)

    def _copy_code(self) -> None:
        QApplication.clipboard().setText(self.code_label.text())

    def _on_authenticated(self, username: str, token: str) -> None:
        self.username = username
        self.token = token
        self.accept()

    def _on_failed(self, message: str) -> None:
        self.instructions_label.setText(f"Login failed: {message}")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

    def _on_cancel(self) -> None:
        if self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(2000)
        self.reject()
