"""Mandatory pre-MainWindow gate: which Project this run is scoped to.

Shown by launcher.py, before plugin discovery/MainWindow construction, only
when core/store.py's LocalConfigStore.active_project_id doesn't already
point at a real project (first run, or the previously active one got
deleted elsewhere) and there's more than one project to choose from — see
launcher.py's own comment for the exact gate logic. Root-level file with no
single domain owner, same as theme_apply.py: used only by launcher.py,
constructed before MainWindow (and everything MainWindow depends on) exists.

Once chosen, the project is fixed for the whole run — there is no dropdown
anywhere else in the app that can change it again; only a full restart back
through this same gate can (plugins/core/project_editor's Settings > Project
tab's "Switch Project...", interface/main_window.py's
_request_switch_project).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout

from core_api import Project


class ProjectSelectorDialog(QDialog):
    def __init__(self, projects: list[Project], parent=None, *, preselect_id: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Select Project")
        self.setMinimumWidth(360)
        # No close button / Escape-to-reject affordance beyond Cancel below —
        # deliberately modal-only: this is the mandatory gate launcher.py
        # refuses to build MainWindow without an answer to (see that
        # module), same posture as the old GitHub login gate before it moved
        # out to UkoreHub.exe.

        self.list_widget = QListWidget()
        for project in projects:
            item = QListWidgetItem(project.name)
            item.setData(Qt.ItemDataRole.UserRole, project.id)
            self.list_widget.addItem(item)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)

        preselect_row = 0
        if preselect_id is not None:
            for row in range(self.list_widget.count()):
                if self.list_widget.item(row).data(Qt.ItemDataRole.UserRole) == preselect_id:
                    preselect_row = row
                    break
        self.list_widget.setCurrentRow(preselect_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self._ok_button = buttons.button(QDialogButtonBox.Ok)
        self._ok_button.setEnabled(self.list_widget.currentItem() is not None)
        self.list_widget.currentItemChanged.connect(
            lambda current, _previous: self._ok_button.setEnabled(current is not None)
        )

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Choose the project to open. UkoreHub will restart to switch projects later."))
        layout.addWidget(self.list_widget)
        layout.addWidget(buttons)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        self.accept()

    def selected_project_id(self) -> str | None:
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None
