from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from plugin_api import MetadataStore, RequirementsTreeWidget, pick_image_file
from plugins.core.project_editor.pipeline_store import Category


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
    """Full Name/URL/Thumbnail/Requirements editor, used as-is for **Add**
    Repo (one-step bootstrap of a new repo record). For **editing** an
    existing repo, Project Editor's node context menu now only asks for
    Name/Git URL here (show_thumbnail=False, no store/project_id) —
    Thumbnail has its own "Change Thumbnail..." context menu action;
    editing Requirements on an existing repo has no UI entry point since
    Repo About was removed."""

    def __init__(
        self,
        parent=None,
        *,
        name: str = "",
        git_url: str = "",
        show_thumbnail: bool = True,
        thumbnail_path: Path | None = None,
        store: MetadataStore | None = None,
        project_id: str | None = None,
        selected_program_ids: list[str] | None = None,
        selected_program_version_pins: dict[str, str] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Edit Repo" if name else "Add Repo")
        self._chosen_thumbnail_path: Path | None = None

        self.name_edit = QLineEdit(name)
        self.git_url_edit = QLineEdit(git_url)
        self.git_url_edit.setPlaceholderText("git@github.com:org/repo.git")

        form = QFormLayout()
        form.addRow("Name:", self.name_edit)
        form.addRow("Git URL:", self.git_url_edit)

        self.thumbnail_preview: QLabel | None = None
        if show_thumbnail:
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
            form.addRow("Thumbnail:", thumbnail_row)

        # See RequirementsTreeWidget for the tree shape (checkable Program
        # nodes with checkable per-version children).
        self.requirements_tree: RequirementsTreeWidget | None = None
        if store is not None and project_id is not None:
            self.requirements_tree = RequirementsTreeWidget(
                store=store,
                project_id=project_id,
                selected_program_ids=selected_program_ids,
                selected_program_version_pins=selected_program_version_pins,
            )
            form.addRow("Requirements:", self.requirements_tree)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_choose_image(self) -> None:
        file_path = pick_image_file(self, "Choose Thumbnail Image")
        if file_path is None:
            return
        self._chosen_thumbnail_path = file_path
        self.thumbnail_preview.setPixmap(QPixmap(str(file_path)))

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

    def selected_program_ids(self) -> list[str]:
        return self.requirements_tree.selected_program_ids() if self.requirements_tree else []

    def selected_program_version_pins(self) -> dict[str, str]:
        return self.requirements_tree.selected_program_version_pins() if self.requirements_tree else {}


class AssignCategoryDialog(QDialog):
    """Node right-click "Assign to Category..." (added 2026-08-19) — a
    single QComboBox listing "(Uncategorized)", every existing Category,
    then "New Category..." (which reveals a name field below it, focused
    automatically). Returns either an existing category id, None
    (Uncategorized), or a brand-new name for
    ProjectGraphView.assign_repo_category to create via
    PipelineStore.add_category — this dialog never talks to PipelineStore
    itself, matching every other dialog in this file (RepoDialog/
    ProjectDialog also just hand back plain values for the caller to act
    on)."""

    _UNCATEGORIZED_DATA = "__uncategorized__"
    _NEW_CATEGORY_DATA = "__new__"

    def __init__(self, parent=None, *, categories: list[Category], current_category_id: str | None):
        super().__init__(parent)
        self.setWindowTitle("Assign to Category")

        self.category_combo = QComboBox()
        self.category_combo.addItem("(Uncategorized)", self._UNCATEGORIZED_DATA)
        for category in categories:
            self.category_combo.addItem(category.name, category.id)
        self.category_combo.addItem("New Category...", self._NEW_CATEGORY_DATA)
        selected_index = self.category_combo.findData(current_category_id or self._UNCATEGORIZED_DATA)
        self.category_combo.setCurrentIndex(selected_index if selected_index >= 0 else 0)

        self.new_name_edit = QLineEdit()
        self.new_name_edit.setPlaceholderText("Category name")

        form = QFormLayout()
        form.addRow("Category:", self.category_combo)
        form.addRow("New Name:", self.new_name_edit)
        self._new_name_label = form.labelForField(self.new_name_edit)

        self.category_combo.currentIndexChanged.connect(self._on_combo_changed)
        self._on_combo_changed()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_combo_changed(self) -> None:
        is_new = self.is_new_category()
        self.new_name_edit.setVisible(is_new)
        if self._new_name_label is not None:
            self._new_name_label.setVisible(is_new)
        if is_new:
            self.new_name_edit.setFocus()

    def _on_accept(self) -> None:
        if self.is_new_category() and not self.new_name_edit.text().strip():
            self.new_name_edit.setFocus()
            return
        self.accept()

    def is_new_category(self) -> bool:
        return self.category_combo.currentData() == self._NEW_CATEGORY_DATA

    def new_category_name(self) -> str:
        return self.new_name_edit.text().strip()

    def selected_category_id(self) -> str | None:
        """None for both "(Uncategorized)" and "New Category..." — the
        latter is meaningless until ProjectGraphView.assign_repo_category
        actually creates the category and gets back its real id."""
        data = self.category_combo.currentData()
        if data in (self._UNCATEGORIZED_DATA, self._NEW_CATEGORY_DATA):
            return None
        return data
