from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from interface.shared.image_asset import pick_image_file


class ProgramDialog(QDialog):
    def __init__(
        self, parent=None, *, name: str = "", version: str = "", description: str = "", icon_path: Path | None = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Edit Program" if name else "Add Program")
        self._chosen_icon_path: Path | None = None

        self.name_edit = QLineEdit(name)
        self.version_edit = QLineEdit(version)
        self.description_edit = QTextEdit(description)
        self.description_edit.setFixedHeight(80)

        self.icon_preview = QLabel("No icon")
        self.icon_preview.setFixedSize(48, 48)
        self.icon_preview.setScaledContents(True)
        if icon_path and icon_path.exists():
            self.icon_preview.setPixmap(QPixmap(str(icon_path)))
        choose_icon_btn = QPushButton("Choose Icon...")
        choose_icon_btn.clicked.connect(self._on_choose_icon)
        icon_row = QHBoxLayout()
        icon_row.addWidget(self.icon_preview)
        icon_row.addWidget(choose_icon_btn)

        form = QFormLayout()
        form.addRow("Name:", self.name_edit)
        form.addRow("Version:", self.version_edit)
        form.addRow("Icon:", icon_row)
        form.addRow("Description:", self.description_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_choose_icon(self) -> None:
        file_path = pick_image_file(self, "Choose Program Icon")
        if file_path is None:
            return
        self._chosen_icon_path = file_path
        self.icon_preview.setPixmap(QPixmap(str(file_path)))

    def _on_accept(self) -> None:
        if not self.name_edit.text().strip():
            return
        self.accept()

    def name(self) -> str:
        return self.name_edit.text().strip()

    def version(self) -> str:
        return self.version_edit.text().strip()

    def description(self) -> str:
        return self.description_edit.toPlainText().strip()

    def chosen_icon_path(self) -> Path | None:
        return self._chosen_icon_path
