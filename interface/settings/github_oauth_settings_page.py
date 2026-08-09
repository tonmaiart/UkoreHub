from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QWidget

from core.store import SystemConfigStore


class GithubOAuthSettingsPage(QWidget):
    """The GitHub OAuth Client ID field, split out of CommonSettingsPage
    into its own Developer-category tab — most users never need to touch
    this, only whoever registered the studio's GitHub OAuth App. The
    Google Cloud Storage sync settings that used to live on this same page
    moved to their own gated window — see
    interface/settings/studio_settings_dialog.py's StudioSettingsDialog,
    opened via Sidebar's separate "Studio Setting" footer button — since
    that config needs a real login gate and an explicit Save step, unlike
    this page's plain self-persisting field."""

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
        hint.setProperty("secondary", True)
        hint.setWordWrap(True)
        form.addRow("", hint)

    def _save_github_client_id(self) -> None:
        self._system_config_store.set_github_client_id(self.client_id_edit.text().strip())
