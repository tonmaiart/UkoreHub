from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QWidget

from core_api import SystemConfigStore
from interface.shared.widget_helpers import set_secondary_text


class GithubOAuthSettingsPage(QWidget):
    """The GitHub OAuth Client ID field, split out of CommonSettingsPage
    into its own Developer-category tab — most users never need to touch
    this, only whoever registered the studio's GitHub OAuth App. Cloud
    sync config used to live on this same page (later moved to its own
    gated `StudioSettingsDialog` window); it has no settings UI at all now
    — a single shared R2 key is baked into `UkoreHubLauncher.exe`, see the
    `ukorehub-cloud-sync` skill."""

    def __init__(self, parent=None, *, system_config_store: SystemConfigStore):
        super().__init__(parent)
        self._system_config_store = system_config_store

        self.client_id_edit = QLineEdit(system_config_store.github_client_id or "")
        self.client_id_edit.setPlaceholderText("From github.com/settings/developers (Device Flow enabled)")
        self.client_id_edit.editingFinished.connect(self._save_github_client_id)

        form = QFormLayout(self)
        form.addRow("GitHub OAuth Client ID:", self.client_id_edit)
        hint = QLabel(
            "Optional — needed only for the mandatory GitHub login step in the\n"
            "launcher (UkoreHub.exe) to work. Register a public OAuth App and\n"
            "enable \"Device Flow\" to get one."
        )
        set_secondary_text(hint)
        hint.setWordWrap(True)
        form.addRow("", hint)

    def _save_github_client_id(self) -> None:
        self._system_config_store.set_github_client_id(self.client_id_edit.text().strip())
