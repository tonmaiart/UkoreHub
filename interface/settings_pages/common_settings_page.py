from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from core.store import LocalConfigStore, SystemConfigStore


class CommonSettingsPage(QWidget):
    def __init__(
        self, parent=None, *, local_config_store: LocalConfigStore, system_config_store: SystemConfigStore
    ):
        super().__init__(parent)
        self._local_config_store = local_config_store
        self._system_config_store = system_config_store

        self.path_edit = QLineEdit(local_config_store.workspace_root or "")
        self.path_edit.editingFinished.connect(self._save_workspace_root)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_btn)
        path_row_widget = QWidget()
        path_row_widget.setLayout(path_row)

        self.client_id_edit = QLineEdit(system_config_store.github_client_id or "")
        self.client_id_edit.setPlaceholderText("From github.com/settings/developers (Device Flow enabled)")
        self.client_id_edit.editingFinished.connect(self._save_github_client_id)

        form = QFormLayout(self)
        form.addRow("Workspace folder:", path_row_widget)
        form.addRow("GitHub OAuth Client ID:", self.client_id_edit)
        hint = QLabel(
            "Optional — needed only for the Login button in the status bar to work.\n"
            "Register a public OAuth App and enable \"Device Flow\" to get one."
        )
        hint.setProperty("secondary", True)
        hint.setWordWrap(True)
        form.addRow("", hint)

    def _browse(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose Workspace Folder", self.path_edit.text())
        if directory:
            self.path_edit.setText(directory)
            self._save_workspace_root()

    def _save_workspace_root(self) -> None:
        self._local_config_store.set_workspace_root(self.path_edit.text().strip())

    def _save_github_client_id(self) -> None:
        self._system_config_store.set_github_client_id(self.client_id_edit.text().strip())
