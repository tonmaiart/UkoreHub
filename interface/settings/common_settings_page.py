from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QPushButton, QWidget

from core.store import LocalConfigStore


class CommonSettingsPage(QWidget):
    # MainWindow connects this to the same logout flow the old Sidebar
    # toggle button used to trigger directly (see interface/main_window.py's
    # _on_logout_requested) — logout lives here now instead of in Sidebar's
    # footer.
    logout_requested = Signal()
    # MainWindow connects this to the same os.execv restart MainWindow's
    # own "Update and Restart" sidebar button already uses (see
    # _on_update_and_restart/_restart_app) — this one just restarts, no
    # git pull first.
    restart_requested = Signal()

    def __init__(self, parent=None, *, local_config_store: LocalConfigStore):
        super().__init__(parent)
        self._local_config_store = local_config_store

        # Workspace folder is fixed to this install's own projects/ folder
        # (forced in launcher.py) — shown here read-only, no Browse option.
        self.workspace_label = QLabel(local_config_store.workspace_root or "")

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout_requested.emit)

        self.restart_button = QPushButton("Restart")
        self.restart_button.clicked.connect(self.restart_requested.emit)

        form = QFormLayout(self)
        form.addRow("Workspace folder:", self.workspace_label)
        form.addRow("Account:", self.logout_button)
        form.addRow("Application:", self.restart_button)
