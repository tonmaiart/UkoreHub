from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class ProjectDialog(QDialog):
    def __init__(self, parent=None, *, name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Edit Project" if name else "Add Project")

        self.name_edit = QLineEdit(name)

        form = QFormLayout()
        form.addRow("Name:", self.name_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        if not self.name_edit.text().strip():
            self.name_edit.setFocus()
            return
        self.accept()

    def name(self) -> str:
        return self.name_edit.text().strip()


class RepoDialog(QDialog):
    def __init__(self, parent=None, *, name: str = "", git_url: str = "", thumbnail_path: Path | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Repo" if name else "Add Repo")
        self._chosen_thumbnail_path: Path | None = None

        self.name_edit = QLineEdit(name)
        self.git_url_edit = QLineEdit(git_url)
        self.git_url_edit.setPlaceholderText("git@github.com:org/repo.git")

        self.thumbnail_preview = QLabel("No image")
        self.thumbnail_preview.setFixedSize(120, 68)
        self.thumbnail_preview.setScaledContents(True)
        if thumbnail_path and thumbnail_path.exists():
            self.thumbnail_preview.setPixmap(QPixmap(str(thumbnail_path)))
        choose_image_btn = QPushButton("Choose Image...")
        choose_image_btn.clicked.connect(self._on_choose_image)
        thumbnail_row = QHBoxLayout()
        thumbnail_row.addWidget(self.thumbnail_preview)
        thumbnail_row.addWidget(choose_image_btn)

        form = QFormLayout()
        form.addRow("Name:", self.name_edit)
        form.addRow("Git URL:", self.git_url_edit)
        form.addRow("Thumbnail:", thumbnail_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_choose_image(self) -> None:
        file_path, _filter = QFileDialog.getOpenFileName(self, "Choose Thumbnail Image", "", "Images (*.png *.jpg *.jpeg)")
        if not file_path:
            return
        self._chosen_thumbnail_path = Path(file_path)
        self.thumbnail_preview.setPixmap(QPixmap(file_path))

    def _on_accept(self) -> None:
        if not self.name_edit.text().strip() or not self.git_url_edit.text().strip():
            return
        self.accept()

    def name(self) -> str:
        return self.name_edit.text().strip()

    def git_url(self) -> str:
        return self.git_url_edit.text().strip()

    def chosen_thumbnail_path(self) -> Path | None:
        return self._chosen_thumbnail_path
