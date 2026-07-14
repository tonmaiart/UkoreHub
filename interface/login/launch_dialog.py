from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.git_service import GitService
from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
from core.github.token_store import TokenStore, TokenStoreFallbackUsed
from interface.login.github_auth_widget import GitHubAuthWidget
from interface.login.github_login_dialog import GitHubLoginDialog
from interface.login.repo_picker import RepoPickerDialog


class LaunchDialog(QDialog):
    """Mandatory GitHub login gate — shown at launch, and again right after
    logout, since the app requires being logged in to use at all. Not
    closable via the window's own close button/Escape/Alt+F4 while logged
    out (see reject()); "Continue" stays disabled until login succeeds."""

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
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.resize(420, 260)
        self.store = store
        self.local_config_store = local_config_store
        self.system_config_store = system_config_store
        self.git_service = git_service
        self.token_store = token_store
        self._login_dialog: GitHubLoginDialog | None = None

        intro = QLabel("Log in with GitHub to continue — UkoreHub requires it.")
        intro.setWordWrap(True)

        self.github_auth_widget = GitHubAuthWidget()
        self.github_auth_widget.login_requested.connect(self._on_login_requested)
        self.github_auth_widget.logout_requested.connect(self._on_logout_requested)

        choose_project_btn = QPushButton("Choose Project...")
        choose_project_btn.clicked.connect(self._on_choose_project)

        self.continue_btn = QPushButton("Continue")
        self.continue_btn.clicked.connect(self._on_continue)

        form = QFormLayout()
        form.addRow("GitHub:", self.github_auth_widget)
        form.addRow("", choose_project_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addLayout(form)
        layout.addStretch()
        layout.addWidget(self.continue_btn)

        self._refresh_login_display()

    def _is_logged_in(self) -> bool:
        return bool(self.local_config_store.github_username and self.token_store.load_token())

    def _refresh_login_display(self) -> None:
        if self._is_logged_in():
            self.github_auth_widget.set_state(self.local_config_store.github_username)
        else:
            self.github_auth_widget.set_state(None)
        self.continue_btn.setEnabled(self._is_logged_in())

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
                "No GitHub OAuth Client ID configured yet. Ask a studio admin to "
                "set one (Setting > Common, reachable once someone is logged in — "
                "or by editing data/system_config.json directly).",
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
            self.continue_btn.setEnabled(True)

    def _on_logout_requested(self) -> None:
        self.token_store.clear_token()
        self.local_config_store.set_github_username(None)
        self.github_auth_widget.set_state(None)
        self.continue_btn.setEnabled(False)

    def _on_continue(self) -> None:
        if self._is_logged_in():
            self.accept()

    def reject(self) -> None:
        # Escape / Alt+F4 (QDialog's default closeEvent calls reject()) —
        # only ever closes the gate once logged in; while logged out there
        # is nothing to cancel back to, so swallow the attempt.
        if self._is_logged_in():
            self.accept()
