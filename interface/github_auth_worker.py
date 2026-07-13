from __future__ import annotations

import webbrowser

from PySide6.QtCore import QThread, Signal

from core.exceptions import GitHubAuthError
from core.github import auth


class GitHubAuthWorker(QThread):
    code_ready = Signal(str, str)
    authenticated = Signal(str, str)
    failed = Signal(str)

    def __init__(self, client_id: str | None, parent=None):
        super().__init__(parent)
        self.client_id = client_id

    def run(self) -> None:
        try:
            if not self.client_id:
                raise GitHubAuthError(
                    "GitHub Client ID not configured — set it in Setting > Common."
                )
            device_code_response = auth.request_device_code(self.client_id)
            self.code_ready.emit(
                device_code_response.user_code, device_code_response.verification_uri
            )
            webbrowser.open(device_code_response.verification_uri)
            token = auth.poll_for_token(
                self.client_id,
                device_code_response.device_code,
                device_code_response.interval,
                device_code_response.expires_in,
            )
            username = auth.fetch_username(token)
            self.authenticated.emit(username, token)
        except GitHubAuthError as exc:
            self.failed.emit(str(exc))
