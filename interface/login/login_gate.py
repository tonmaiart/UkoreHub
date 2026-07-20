from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QWidget

from core.git_service import GitService
from core.github.token_store import TokenStore
from core.store import LocalConfigStore, SystemConfigStore
from interface.login.github_auth_widget import GitHubAuthWidget
from interface.login.login_overlay import LoginOverlay


class LoginGate:
    """Owns the mandatory GitHub-login gate's mechanics — constructing
    LoginOverlay, checking the saved token/username on launch, restoring
    session state into Sidebar's account widget + GitService, and clearing
    everything on logout — so main_window.py doesn't need to hold any of
    this itself. MainWindow still drives *when* to show/teardown the gate
    and owns setCentralWidget/takeCentralWidget (window-layout concerns,
    not login ones) — see its _show_login_gate/_teardown_login_gate."""

    def __init__(
        self,
        *,
        system_config_store: SystemConfigStore,
        local_config_store: LocalConfigStore,
        token_store: TokenStore,
        git_service: GitService,
    ):
        self._system_config_store = system_config_store
        self._local_config_store = local_config_store
        self._token_store = token_store
        self._git_service = git_service
        self.overlay: LoginOverlay | None = None

    def is_logged_in(self) -> bool:
        return bool(self._local_config_store.github_username and self._token_store.load_token())

    def show(self, parent: QWidget, on_completed: Callable[[], None]) -> LoginOverlay:
        self.overlay = LoginOverlay(
            parent,
            system_config_store=self._system_config_store,
            local_config_store=self._local_config_store,
            token_store=self._token_store,
        )
        self.overlay.login_completed.connect(on_completed)
        return self.overlay

    def teardown(self) -> None:
        if self.overlay is not None:
            self.overlay.deleteLater()
            self.overlay = None

    def restore_session_state(self, github_auth_widget: GitHubAuthWidget) -> None:
        token = self._token_store.load_token()
        if self._local_config_store.github_username and token:
            github_auth_widget.set_state(self._local_config_store.github_username)
            self._git_service.set_github_token(token)
        else:
            self._local_config_store.set_github_username(None)
            github_auth_widget.set_state(None)
            self._git_service.set_github_token(None)

    def logout(self, github_auth_widget: GitHubAuthWidget) -> None:
        self._token_store.clear_token()
        self._local_config_store.set_github_username(None)
        github_auth_widget.set_state(None)
        self._git_service.set_github_token(None)
