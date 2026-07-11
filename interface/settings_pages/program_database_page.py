from __future__ import annotations

import shutil

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import UkoreHubError
from core.program_store import ProgramStore
from interface.program_dialog import ProgramDialog


class ProgramDatabasePage(QWidget):
    def __init__(self, parent=None, *, program_store: ProgramStore):
        super().__init__(parent)
        self.program_store = program_store

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
        layout.addLayout(button_row)
        layout.addWidget(self.list_widget)

        self.refresh_list()

    def refresh_list(self) -> None:
        self.list_widget.clear()
        for program in self.program_store.list_programs():
            item = QListWidgetItem(program.name)
            item.setData(Qt.UserRole, program.id)
            icon_path = self.program_store.resolve_icon_path(program)
            if icon_path and icon_path.exists():
                item.setIcon(QIcon(str(icon_path)))
            self.list_widget.addItem(item)

    def _selected_program_id(self) -> str | None:
        items = self.list_widget.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.UserRole)

    def _on_add(self) -> None:
        dialog = ProgramDialog(self)
        if dialog.exec():
            try:
                program = self.program_store.add_program(dialog.name(), dialog.description())
            except UkoreHubError as exc:
                QMessageBox.warning(self, "Add Program", str(exc))
                return
            if dialog.chosen_icon_path():
                self._save_icon(program.id, dialog.chosen_icon_path())
            self.refresh_list()

    def _on_edit(self) -> None:
        program_id = self._selected_program_id()
        if not program_id:
            QMessageBox.information(self, "Edit", "Select a program first.")
            return
        program = self.program_store.get_program(program_id)
        dialog = ProgramDialog(
            self,
            name=program.name,
            description=program.description,
            icon_path=self.program_store.resolve_icon_path(program),
        )
        if dialog.exec():
            try:
                self.program_store.edit_program(program_id, name=dialog.name(), description=dialog.description())
            except UkoreHubError as exc:
                QMessageBox.warning(self, "Edit Program", str(exc))
                return
            if dialog.chosen_icon_path():
                self._save_icon(program_id, dialog.chosen_icon_path())
            self.refresh_list()

    def _on_delete(self) -> None:
        program_id = self._selected_program_id()
        if not program_id:
            QMessageBox.information(self, "Delete", "Select a program first.")
            return
        program = self.program_store.get_program(program_id)
        confirm = QMessageBox.warning(
            self,
            "Delete Program",
            f"Delete '{program.name}' from the Program Database for EVERYONE at the studio?\n\n"
            "Repos that require it will keep referencing it by ID until re-edited. This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.program_store.delete_program(program_id)
            self.refresh_list()

    def _save_icon(self, program_id: str, source_path) -> None:
        icons_dir = self.program_store.icons_dir
        icons_dir.mkdir(parents=True, exist_ok=True)
        ext = source_path.suffix or ".png"
        dest_path = icons_dir / f"{program_id}{ext}"
        try:
            shutil.copyfile(source_path, dest_path)
        except OSError as exc:
            QMessageBox.warning(self, "Icon", f"Could not save icon: {exc}")
            return
        self.program_store.set_program_icon(program_id, dest_path.name)
