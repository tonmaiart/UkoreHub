from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from core.addon_store import AddonMetadataStore, group_addon_ids_by_program
from core.extensibility.loader import DiscoveredPlugin, plugin_source
from core.program_store import ProgramStore
from interface.shared.image_asset import pick_image_file

_NODE_KIND_ROLE = Qt.UserRole + 1


class RequirementsTreeWidget(QTreeWidget):
    """One tree instead of two flat lists: each Program is a checkable
    top-level node (check = required), with the add-ons that declare it as
    a required program nested underneath as checkable children (check =
    enabled). An add-on with no declared required program — or whose
    declared program isn't in the catalog — lands under a trailing "Other
    Add-ons" node instead of being hidden. Shared by RepoDialog (repo
    creation) and RequirementsEditDialog (editing an existing repo's
    requirements from About > Requirement) so both stay in sync."""

    def __init__(
        self,
        parent=None,
        *,
        program_store: ProgramStore,
        addon_catalog: list[DiscoveredPlugin],
        addon_store: AddonMetadataStore | None = None,
        selected_program_ids: list[str] | None = None,
        selected_addon_ids: list[str] | None = None,
    ):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self._addon_items: dict[str, list[QTreeWidgetItem]] = {}

        selected_program_id_set = set(selected_program_ids or [])
        selected_addon_id_set = set(selected_addon_ids or [])
        addon_by_id = {discovered.manifest.id: discovered for discovered in addon_catalog}
        if addon_store is not None:
            by_program, ungrouped = group_addon_ids_by_program(list(addon_by_id.keys()), addon_store)
        else:
            by_program, ungrouped = {}, list(addon_by_id.keys())

        for program in program_store.list_programs():
            version_suffix = f" (v{program.version})" if program.version else ""
            program_item = QTreeWidgetItem([f"{program.name}{version_suffix}"])
            program_item.setFlags(program_item.flags() | Qt.ItemIsUserCheckable)
            program_item.setCheckState(0, Qt.Checked if program.id in selected_program_id_set else Qt.Unchecked)
            program_item.setData(0, Qt.UserRole, program.id)
            program_item.setData(0, _NODE_KIND_ROLE, "program")
            icon_path = program_store.resolve_icon_path(program)
            if icon_path and icon_path.exists():
                program_item.setIcon(0, QIcon(str(icon_path)))
            for addon_id in by_program.get(program.id, []):
                addon_item = self._make_addon_tree_item(addon_by_id[addon_id], addon_id in selected_addon_id_set)
                program_item.addChild(addon_item)
                self._addon_items.setdefault(addon_id, []).append(addon_item)
            self.addTopLevelItem(program_item)
            program_item.setExpanded(True)

        if ungrouped:
            other_item = QTreeWidgetItem(["Other Add-ons"])
            other_item.setData(0, _NODE_KIND_ROLE, "group")
            for addon_id in ungrouped:
                addon_item = self._make_addon_tree_item(addon_by_id[addon_id], addon_id in selected_addon_id_set)
                other_item.addChild(addon_item)
                self._addon_items.setdefault(addon_id, []).append(addon_item)
            self.addTopLevelItem(other_item)
            other_item.setExpanded(True)

        self.itemChanged.connect(self._on_tree_item_changed)

    def _make_addon_tree_item(self, discovered: DiscoveredPlugin, checked: bool) -> QTreeWidgetItem:
        manifest = discovered.manifest
        item = QTreeWidgetItem([f"{manifest.name} ({plugin_source(discovered)})"])
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        item.setData(0, Qt.UserRole, manifest.id)
        item.setData(0, _NODE_KIND_ROLE, "addon")
        return item

    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        # An add-on that declares multiple required programs appears as a
        # duplicate leaf under each matching program node — keep every
        # duplicate's check state in sync so it reads as one toggle.
        if item.data(0, _NODE_KIND_ROLE) != "addon":
            return
        addon_id = item.data(0, Qt.UserRole)
        state = item.checkState(0)
        for sibling in self._addon_items.get(addon_id, []):
            if sibling is not item and sibling.checkState(0) != state:
                sibling.setCheckState(0, state)

    def selected_program_ids(self) -> list[str]:
        selected = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, _NODE_KIND_ROLE) == "program" and item.checkState(0) == Qt.Checked:
                selected.append(item.data(0, Qt.UserRole))
        return selected

    def selected_addon_ids(self) -> list[str]:
        return [
            addon_id
            for addon_id, items in self._addon_items.items()
            if items and items[0].checkState(0) == Qt.Checked
        ]


class RequirementsEditDialog(QDialog):
    """Standalone edit-only entry point onto RequirementsTreeWidget, used
    by About > Requirement to edit an existing repo's required Programs /
    enabled Add-ons in place — see interface/about/repo_about_page.py.
    RepoDialog below still owns the tree at repo-creation time."""

    def __init__(
        self,
        parent=None,
        *,
        program_store: ProgramStore,
        addon_catalog: list[DiscoveredPlugin],
        addon_store: AddonMetadataStore | None = None,
        selected_program_ids: list[str] | None = None,
        selected_addon_ids: list[str] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Edit Requirements")

        self.requirements_tree = RequirementsTreeWidget(
            program_store=program_store,
            addon_catalog=addon_catalog,
            addon_store=addon_store,
            selected_program_ids=selected_program_ids,
            selected_addon_ids=selected_addon_ids,
        )

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.requirements_tree)
        layout.addWidget(buttons)

    def selected_program_ids(self) -> list[str]:
        return self.requirements_tree.selected_program_ids()

    def selected_addon_ids(self) -> list[str]:
        return self.requirements_tree.selected_addon_ids()


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
    Name/Git URL here (show_thumbnail=False, no program_store/addon_catalog) —
    Thumbnail and Requirements/Add-ons moved to About > About and
    About > Requirement respectively, see interface/about/repo_about_page.py."""

    def __init__(
        self,
        parent=None,
        *,
        name: str = "",
        git_url: str = "",
        show_thumbnail: bool = True,
        thumbnail_path: Path | None = None,
        program_store: ProgramStore | None = None,
        selected_program_ids: list[str] | None = None,
        addon_catalog: list[DiscoveredPlugin] | None = None,
        addon_store: AddonMetadataStore | None = None,
        selected_addon_ids: list[str] | None = None,
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

        # See RequirementsTreeWidget for the tree shape (Program nodes with
        # nested Add-on children, checkable both levels).
        self.requirements_tree: RequirementsTreeWidget | None = None
        if program_store is not None and addon_catalog is not None:
            self.requirements_tree = RequirementsTreeWidget(
                program_store=program_store,
                addon_catalog=addon_catalog,
                addon_store=addon_store,
                selected_program_ids=selected_program_ids,
                selected_addon_ids=selected_addon_ids,
            )
            form.addRow("Requirements / Add-ons:", self.requirements_tree)

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

    def selected_addon_ids(self) -> list[str]:
        return self.requirements_tree.selected_addon_ids() if self.requirements_tree else []
