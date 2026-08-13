from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core_api import ConflictError, LocalConfigStore, MetadataStore, UkoreHubError
from interface.settings.program_dialog import ProgramDialog
from interface.shared.image_asset import save_image_asset
from interface.shared.widget_helpers import confirm_action


class ProgramDatabasePage(QWidget):
    """Settings > Project > Program Database — each Project has its own
    catalog of pipeline software (core/models.py's Project.programs), not
    shared with other Projects. As of the single-project-per-session
    change, this always operates on local_config_store.active_project_id —
    the one project fixed for the whole run by launcher.py's mandatory
    Project Selector gate — rather than its own independent project
    picker (removed; there's nothing to pick anymore, every page in the
    app reads through the same fixed project id now)."""

    def __init__(self, parent=None, *, store: MetadataStore, local_config_store: LocalConfigStore):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store

        self.project_label = QLabel()

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)

        add_btn = QPushButton("Add Program")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        add_btn.clicked.connect(self._on_add)
        edit_btn.clicked.connect(self._on_edit)
        delete_btn.clicked.connect(self._on_delete)

        button_row = QHBoxLayout()
        for button in (add_btn, edit_btn, delete_btn):
            button_row.addWidget(button)
        button_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Project:"))
        layout.addWidget(self.project_label)
        layout.addLayout(button_row)
        layout.addWidget(self.list_widget)

        self.refresh()

    def refresh(self) -> None:
        """Re-reads the active project's current name and reloads its
        Program list. Called on construction and via
        SettingsTabSpec.on_activated."""
        project_id = self._selected_project_id()
        project = self.store.get_project(project_id) if project_id else None
        self.project_label.setText(project.name if project is not None else "(no project)")
        self.refresh_list()

    def _selected_project_id(self) -> str | None:
        return self.local_config_store.active_project_id

    def refresh_list(self) -> None:
        self.list_widget.clear()
        project_id = self._selected_project_id()
        if project_id is None:
            return
        for program in self.store.list_programs(project_id):
            label = f"{program.name} (v{', '.join(program.versions)})" if program.versions else program.name
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, program.id)
            icon_path = self.store.resolve_program_icon_path(program)
            if icon_path and icon_path.exists():
                item.setIcon(QIcon(str(icon_path)))
            self.list_widget.addItem(item)

    def _selected_program_id(self) -> str | None:
        items = self.list_widget.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.UserRole)

    def _on_add(self) -> None:
        project_id = self._selected_project_id()
        if project_id is None:
            QMessageBox.information(self, "Add Program", "Select a project first.")
            return
        dialog = ProgramDialog(self)
        if dialog.exec():
            try:
                program = self.store.add_program(project_id, dialog.name(), dialog.description(), dialog.versions())
            except ConflictError as exc:
                self.store.load()
                QMessageBox.warning(self, "Add Program", str(exc))
                self.refresh_list()
                return
            except UkoreHubError as exc:
                QMessageBox.warning(self, "Add Program", str(exc))
                return
            if dialog.chosen_icon_path():
                self._save_icon(project_id, program.id, dialog.chosen_icon_path())
            self.refresh_list()

    def _on_edit(self) -> None:
        project_id = self._selected_project_id()
        program_id = self._selected_program_id()
        if project_id is None or not program_id:
            QMessageBox.information(self, "Edit", "Select a program first.")
            return
        program = self.store.get_program(project_id, program_id)
        dialog = ProgramDialog(
            self,
            name=program.name,
            versions=program.versions,
            description=program.description,
            icon_path=self.store.resolve_program_icon_path(program),
        )
        if dialog.exec():
            try:
                self.store.edit_program(
                    project_id,
                    program_id,
                    name=dialog.name(),
                    description=dialog.description(),
                    versions=dialog.versions(),
                )
            except ConflictError as exc:
                self.store.load()
                QMessageBox.warning(self, "Edit Program", str(exc))
                self.refresh_list()
                return
            except UkoreHubError as exc:
                QMessageBox.warning(self, "Edit Program", str(exc))
                return
            if dialog.chosen_icon_path():
                self._save_icon(project_id, program_id, dialog.chosen_icon_path())
            self.refresh_list()

    def _on_delete(self) -> None:
        project_id = self._selected_project_id()
        program_id = self._selected_program_id()
        if project_id is None or not program_id:
            QMessageBox.information(self, "Delete", "Select a program first.")
            return
        project = self.store.get_project(project_id)
        program = self.store.get_program(project_id, program_id)
        confirmed = confirm_action(
            self,
            "Delete Program",
            f"Delete '{program.name}' from '{project.name}''s Program Database?\n\n"
            "Repos that require it will keep referencing it by ID until re-edited. This cannot be undone.",
        )
        if confirmed:
            try:
                self.store.delete_program(project_id, program_id)
            except ConflictError as exc:
                self.store.load()
                QMessageBox.warning(self, "Delete Program", str(exc))
            self.refresh_list()

    def _save_icon(self, project_id: str, program_id: str, source_path) -> None:
        filename = save_image_asset(
            self, source_path=source_path, dest_dir=self.store.program_icons_dir, asset_id=program_id
        )
        if filename is not None:
            self.store.set_program_icon(project_id, program_id, filename)
