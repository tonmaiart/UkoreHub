from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.git_service import GitService
from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
from core.token_store import TokenStore, TokenStoreFallbackUsed
from interface.github_auth_widget import GitHubAuthWidget
from interface.github_login_dialog import GitHubLoginDialog
from interface.repo_picker import RepoPickerDialog


class LaunchDialog(QDialog):
    """Skippable "Quick Start" shown while the user isn't logged in yet —
    GitHub login, workspace folder, and a quick project pick, all optional."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        system_config_store: SystemConfigStore,
        git_service: GitService,
        token_store: TokenStore,
    ):
        super().__init__(parent)
        self.setWindowTitle("Welcome to UkoreHub")
        self.resize(420, 260)
        self.store = store
        self.local_config_store = local_config_store
        self.system_config_store = system_config_store
        self.git_service = git_service
        self.token_store = token_store
        self._login_dialog: GitHubLoginDialog | None = None

        intro = QLabel("Quick Start — set these up now, or just Continue and do it later.")
        intro.setWordWrap(True)

        self.github_auth_widget = GitHubAuthWidget()
        self.github_auth_widget.login_requested.connect(self._on_login_requested)
        self.github_auth_widget.logout_requested.connect(self._on_logout_requested)
        self._refresh_login_display()

        self.workspace_edit = QLineEdit(local_config_store.workspace_root or "")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse_workspace)
        workspace_row = QHBoxLayout()
        workspace_row.addWidget(self.workspace_edit, stretch=1)
        workspace_row.addWidget(browse_btn)

        choose_project_btn = QPushButton("Choose Project...")
        choose_project_btn.clicked.connect(self._on_choose_project)

        continue_btn = QPushButton("Continue")
        continue_btn.clicked.connect(self._on_continue)

        form = QFormLayout()
        form.addRow("GitHub:", self.github_auth_widget)
        form.addRow("Workspace Folder:", workspace_row)
        form.addRow("", choose_project_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addLayout(form)
        layout.addStretch()
        layout.addWidget(continue_btn)

    def _refresh_login_display(self) -> None:
        if self.local_config_store.github_username and self.token_store.load_token():
            self.github_auth_widget.set_state(self.local_config_store.github_username)
        else:
            self.github_auth_widget.set_state(None)

    def _on_browse_workspace(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose Workspace Folder", self.workspace_edit.text())
        if directory:
            self.workspace_edit.setText(directory)

    def _on_choose_project(self) -> None:
        dialog = RepoPickerDialog(self, store=self.store)
        if dialog.exec():
            project_id = dialog.selected_project_id()
            repo_id = dialog.selected_repo_id()
            if project_id and repo_id:
                self.local_config_store.set_active_repo(project_id, repo_id)

    def _on_login_requested(self) -> None:
        if not self.system_config_store.github_client_id:
            QMessageBox.information(
                self,
                "GitHub Login",
                "No GitHub OAuth Client ID configured yet — set it later in Setting > Common.",
            )
            return
        self._login_dialog = GitHubLoginDialog(self, client_id=self.system_config_store.github_client_id)
        if self._login_dialog.exec():
            username = self._login_dialog.username
            token = self._login_dialog.token
            try:
                self.token_store.save_token(token)
            except TokenStoreFallbackUsed as exc:
                QMessageBox.warning(self, "GitHub Login", str(exc))
            self.local_config_store.set_github_username(username)
            self.github_auth_widget.set_state(username)

    def _on_logout_requested(self) -> None:
        self.token_store.clear_token()
        self.local_config_store.set_github_username(None)
        self.github_auth_widget.set_state(None)

    def _on_continue(self) -> None:
        typed_path = self.workspace_edit.text().strip()
        if typed_path:
            self.local_config_store.set_workspace_root(typed_path)
        self.accept()
