from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QWidget

from core.store import LocalConfigStore, SystemConfigStore


class CommonSettingsPage(QWidget):
    def __init__(
        self, parent=None, *, local_config_store: LocalConfigStore, system_config_store: SystemConfigStore
    ):
        super().__init__(parent)
        self._local_config_store = local_config_store
        self._system_config_store = system_config_store

        # Workspace folder is fixed to this install's own projects/ folder
        # (forced in launcher.py) — shown here read-only, no Browse option.
        self.workspace_label = QLabel(local_config_store.workspace_root or "")

        self.client_id_edit = QLineEdit(system_config_store.github_client_id or "")
        self.client_id_edit.setPlaceholderText("From github.com/settings/developers (Device Flow enabled)")
        self.client_id_edit.editingFinished.connect(self._save_github_client_id)

        form = QFormLayout(self)
        form.addRow("Workspace folder:", self.workspace_label)
        form.addRow("GitHub OAuth Client ID:", self.client_id_edit)
        hint = QLabel(
            "Optional — needed only for the Login button in the status bar to work.\n"
            "Register a public OAuth App and enable \"Device Flow\" to get one."
        )
        hint.setProperty("secondary", True)
        hint.setWordWrap(True)
        form.addRow("", hint)

    def _save_github_client_id(self) -> None:
        self._system_config_store.set_github_client_id(self.client_id_edit.text().strip())
