from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from plugin_api import MetadataStore, NotFoundError, RequirementsTreeWidget, pick_image_file
from plugins.core.project_editor.pipeline_store import Category, CustomPath, PipelineStore, RepoRef


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
    itself, matching every other dialog in this file (RepoDialog also just
    hands back plain values for the caller to act on)."""

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
        latter is meaningless until the caller actually creates the
        category and gets back its real id."""
        data = self.category_combo.currentData()
        if data in (self._UNCATEGORIZED_DATA, self._NEW_CATEGORY_DATA):
            return None
        return data


class EditInfoDialog(QDialog):
    """The Info panel's "Edit Info..." popup (pushButton_edit_info in
    ProjectEditorTabWindows.ui) — a big plain-text editor for one repo's
    free-form info note (PipelineStore.get_repo_info/set_repo_info, stored
    on Repo.plugin_data same as every other per-repo field this plugin
    owns, so it rides along on that project's own already-cloud-synced
    blob with no extra sync plumbing needed). Hands the caller back plain
    text on accept, same as every other dialog in this file — never talks
    to PipelineStore itself."""

    def __init__(self, parent=None, *, text: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Edit Info")
        self.resize(520, 420)

        self.text_edit = QPlainTextEdit(text)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit)
        layout.addWidget(buttons)

    def text(self) -> str:
        return self.text_edit.toPlainText()


class ConnectInputPathDialog(QDialog):
    """Compact single-window replacement for the old two-dialog
    RepoPickerDialog -> CustomPathPickerDialog flow that used to live behind
    the old node graph's "Connect Pipeline Input Path..." node context-menu
    action (removed 2026-07-19, the graph itself removed later, 2026-08-19)
    — one repo combo box plus one custom-path combo box, refreshed together
    in a single small window instead of two separate modal round-trips
    through a heavy thumbnail-card picker. Also picks this connection's
    `direction` (added 2026-07-19) — purely cosmetic (see RepoRef.direction's
    docstring): it only decides which end of the drawn edge gets the
    arrowhead in the Graph View, never the layout/topology. Moved here from
    the former custom_paths_settings_page.py 2026-09-01 when that file was
    folded into project_editor_settings_page.py's merged Settings tab."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        pipeline_store: PipelineStore,
        exclude_project_id: str,
        exclude_repo_id: str,
        initial_ref: RepoRef | None = None,
        title: str = "Connect Input Path",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(380, 220)
        self._store = store
        self._pipeline_store = pipeline_store
        self._repo_ids: list[tuple[str, str]] = []
        self._custom_paths: list[CustomPath] = []

        self.repo_combo = QComboBox()
        for project in store.list_projects():
            for repo in project.repos:
                if project.id == exclude_project_id and repo.id == exclude_repo_id:
                    continue
                self.repo_combo.addItem(f"{project.name} / {repo.name}")
                self._repo_ids.append((project.id, repo.id))
        self.repo_combo.currentIndexChanged.connect(self._on_repo_changed)

        self.path_combo = QComboBox()

        self.input_radio = QRadioButton("Input — arrow points into this repo")
        self.input_radio.setChecked(True)
        self.output_radio = QRadioButton("Output — arrow points out to the target repo")

        self.hint_label = QLabel("")
        self.hint_label.setWordWrap(True)
        self.hint_label.setVisible(False)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Repo:"))
        layout.addWidget(self.repo_combo)
        layout.addWidget(QLabel("Custom Path:"))
        layout.addWidget(self.path_combo)
        layout.addWidget(QLabel("Direction:"))
        layout.addWidget(self.input_radio)
        layout.addWidget(self.output_radio)
        layout.addWidget(self.hint_label)
        layout.addStretch()
        layout.addWidget(self.buttons)

        if self._repo_ids:
            self._on_repo_changed(0)
            if initial_ref is not None:
                self._apply_initial_ref(initial_ref)
        else:
            self.hint_label.setText("No other repos exist yet.")
            self.hint_label.setVisible(True)
            self.repo_combo.setEnabled(False)
            self.path_combo.setEnabled(False)
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)

    def _apply_initial_ref(self, ref: RepoRef) -> None:
        """Pre-selects everything to match an existing connection — used
        when this dialog is opened to Edit one (see
        CustomPathsSettingsPage._on_edit_connection) rather than create a
        new one. A no-op for anything that can no longer be found (e.g.
        the target repo or its custom path was deleted since this
        connection was made) — the dialog just falls back to its normal
        default selection for that part."""
        for index, (project_id, repo_id) in enumerate(self._repo_ids):
            if project_id == ref.project_id and repo_id == ref.repo_id:
                self.repo_combo.setCurrentIndex(index)
                break
        for index, custom_path in enumerate(self._custom_paths):
            if custom_path.id == ref.custom_path_id:
                self.path_combo.setCurrentIndex(index)
                break
        if ref.direction == "output":
            self.output_radio.setChecked(True)
        else:
            self.input_radio.setChecked(True)

    def _on_repo_changed(self, index: int) -> None:
        self.path_combo.clear()
        self._custom_paths = []
        if not (0 <= index < len(self._repo_ids)):
            return
        project_id, repo_id = self._repo_ids[index]
        self._custom_paths = self._pipeline_store.get_custom_paths(project_id, repo_id)
        if not self._custom_paths:
            try:
                repo_name = self._store.get_repo(project_id, repo_id).name
            except NotFoundError:
                repo_name = "This repo"
            self.hint_label.setText(
                f"{repo_name} has no Custom Paths declared yet — switch to it and add one under its own "
                "Repository Setting > Custom Paths > Create This Repo Custom Path first."
            )
            self.hint_label.setVisible(True)
            self.path_combo.setEnabled(False)
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)
            return
        self.hint_label.setVisible(False)
        self.path_combo.setEnabled(True)
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(True)
        for custom_path in self._custom_paths:
            self.path_combo.addItem(f"{custom_path.label}  ({custom_path.path})")

    def selected_ref(self) -> tuple[str, str, str] | None:
        repo_index = self.repo_combo.currentIndex()
        path_index = self.path_combo.currentIndex()
        if not (0 <= repo_index < len(self._repo_ids)) or not (0 <= path_index < len(self._custom_paths)):
            return None
        project_id, repo_id = self._repo_ids[repo_index]
        return project_id, repo_id, self._custom_paths[path_index].id

    def selected_direction(self) -> str:
        return "output" if self.output_radio.isChecked() else "input"


class CustomPathEditDialog(QDialog):
    """Add/Edit dialog for one of this repo's own declared CustomPath
    entries — used by tableWidget_currrent_repo_custom_path's Add/Edit
    buttons (ProjectEditorSettingsWindow.ui). Replaces the old
    always-visible label/path input row + separate "Rename"/"Edit Path" row
    actions with a single small dialog, matching how ConnectInputPathDialog
    already handles the "Connected Custom Path" side."""

    def __init__(
        self,
        parent=None,
        *,
        repo_root: Path,
        label: str = "",
        path: str = "",
        title: str = "Add Custom Path",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._repo_root = repo_root

        self.label_edit = QLineEdit(label)
        self.label_edit.setPlaceholderText("Label (e.g. Character)")
        self.path_edit = QLineEdit(path)
        self.path_edit.setPlaceholderText("Path relative to this repo's root (e.g. Character)")
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._on_browse)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit, stretch=1)
        path_row.addWidget(browse_button)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Label:"))
        layout.addWidget(self.label_edit)
        layout.addWidget(QLabel("Path:"))
        layout.addLayout(path_row)
        layout.addStretch()
        layout.addWidget(self.buttons)

    def _on_browse(self) -> None:
        """Rooted at the active repo's own folder; rejects a folder picked
        from outside it, since CustomPath.path is always relative to the
        repo's own root. Auto-fills the label from the folder name too if
        the label field is still empty."""
        chosen = QFileDialog.getExistingDirectory(self, "Choose Folder", str(self._repo_root))
        if not chosen:
            return
        chosen_path = Path(chosen)
        try:
            relative = chosen_path.relative_to(self._repo_root)
        except ValueError:
            QMessageBox.information(
                self,
                "Choose Folder",
                "Pick a folder inside this repo's own root — Custom Paths are always relative to it.",
            )
            return
        self.path_edit.setText(str(relative).replace("\\", "/"))
        if not self.label_edit.text().strip():
            self.label_edit.setText(chosen_path.name)

    def _on_accept(self) -> None:
        if not self.label_edit.text().strip() or not self.path_edit.text().strip():
            QMessageBox.information(self, self.windowTitle(), "Enter both a label and a path.")
            return
        self.accept()

    def result_values(self) -> tuple[str, str]:
        return self.label_edit.text().strip(), self.path_edit.text().strip()
