from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout

from core.vcs.paths import extract_git_repo_name


class CatalogEntryDialog(QDialog):
    """Add/Edit form for one External Plugins catalog entry — same shape as
    interface/settings/program_dialog.py's ProgramDialog."""

    def __init__(self, parent=None, *, name: str = "", git_url: str = "", folder_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Edit External Plugin" if name else "Add External Plugin")

        self.name_edit = QLineEdit(name)
        self.git_url_edit = QLineEdit(git_url)
        self.git_url_edit.setPlaceholderText("https://github.com/tonmaiart/YourRepo.git")
        self.git_url_edit.textChanged.connect(self._on_git_url_changed)
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

    def _on_git_url_changed(self, git_url: str) -> None:
        # Only auto-fill fields the user hasn't already typed something
        # into themselves — never overwrite an explicit Name/Folder Name.
        git_url = git_url.strip()
        if not git_url:
            return
        derived = extract_git_repo_name(git_url)
        if not self.name_edit.text().strip():
            self.name_edit.setText(derived)
        if not self.folder_name_edit.text().strip():
            self.folder_name_edit.setText(derived)

    def _on_accept(self) -> None:
        git_url = self.git_url_edit.text().strip()
        if not git_url:
            return
        if not self.name_edit.text().strip():
            self.name_edit.setText(extract_git_repo_name(git_url))
        if not self.folder_name_edit.text().strip():
            self.folder_name_edit.setText(extract_git_repo_name(git_url))
        self.accept()

    def name(self) -> str:
        return self.name_edit.text().strip()

    def git_url(self) -> str:
        return self.git_url_edit.text().strip()

    def folder_name(self) -> str:
        return self.folder_name_edit.text().strip()
