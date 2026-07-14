from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)


class CommitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Commit Changes")
        self.resize(420, 260)

        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("Commit message...")
        self.amend_checkbox = QCheckBox("Amend previous commit")
        self.amend_checkbox.toggled.connect(self._update_ok_enabled)
        self.message_edit.textChanged.connect(self._update_ok_enabled)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Commit message:"))
        layout.addWidget(self.message_edit)
        layout.addWidget(self.amend_checkbox)
        layout.addWidget(self.buttons)

        self._update_ok_enabled()

    def _update_ok_enabled(self) -> None:
        ok_button = self.buttons.button(QDialogButtonBox.Ok)
        ok_button.setEnabled(bool(self.message().strip()) or self.amend_checkbox.isChecked())

    def message(self) -> str:
        return self.message_edit.toPlainText().strip()

    def amend(self) -> bool:
        return self.amend_checkbox.isChecked()
