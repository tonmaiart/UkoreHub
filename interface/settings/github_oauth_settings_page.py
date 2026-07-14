from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QWidget

from core.store import SystemConfigStore


class GithubOAuthSettingsPage(QWidget):
    """The GitHub OAuth Client ID field, split out of CommonSettingsPage
    into its own Developer-category tab — most users never need to touch
    this, only whoever registered the studio's GitHub OAuth App."""

    def __init__(self, parent=None, *, system_config_store: SystemConfigStore):
        super().__init__(parent)
        self._system_config_store = system_config_store

        self.client_id_edit = QLineEdit(system_config_store.github_client_id or "")
        self.client_id_edit.setPlaceholderText("From github.com/settings/developers (Device Flow enabled)")
        self.client_id_edit.editingFinished.connect(self._save_github_client_id)

        form = QFormLayout(self)
        form.addRow("GitHub OAuth Client ID:", self.client_id_edit)
        hint = QLabel(
            "Optional — needed only for the mandatory GitHub login gate to work.\n"
            "Register a public OAuth App and enable \"Device Flow\" to get one."
        )
        hint.setProperty("secondary", True)
        hint.setWordWrap(True)
        form.addRow("", hint)

    def _save_github_client_id(self) -> None:
        self._system_config_store.set_github_client_id(self.client_id_edit.text().strip())
