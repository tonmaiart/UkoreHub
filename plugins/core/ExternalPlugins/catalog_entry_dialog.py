from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout


class CatalogEntryDialog(QDialog):
    """Add/Edit form for one External Plugins catalog entry — same shape as
    interface/settings/program_dialog.py's ProgramDialog."""

    def __init__(self, parent=None, *, name: str = "", git_url: str = "", folder_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Edit External Plugin" if name else "Add External Plugin")

        self.name_edit = QLineEdit(name)
        self.git_url_edit = QLineEdit(git_url)
        self.git_url_edit.setPlaceholderText("https://github.com/tonmaiart/YourRepo.git")
        self.folder_name_edit = QLineEdit(folder_name)
        self.folder_name_edit.setPlaceholderText("Folder under cache/plugins/, e.g. YourRepo")

        form = QFormLayout()
        form.addRow("Name:", self.name_edit)
        form.addRow("Git URL:", self.git_url_edit)
        form.addRow("Folder Name:", self.folder_name_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        if not self.name_edit.text().strip() or not self.git_url_edit.text().strip() or not self.folder_name_edit.text().strip():
            return
        self.accept()

    def name(self) -> str:
        return self.name_edit.text().strip()

    def git_url(self) -> str:
        return self.git_url_edit.text().strip()

    def folder_name(self) -> str:
        return self.folder_name_edit.text().strip()
