from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QMessageBox, QPushButton, QVBoxLayout, QWidget

from core.addon_store import AddonMetadataStore
from core.exceptions import UkoreHubError
from core.extensibility.loader import DiscoveredPlugin
from core.models import Project, Repo
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore
from interface.settings_tab_registry import SettingsTabRegistry
from plugins.studio.project_editor.dialogs import ProjectDialog
from interface.shared.widget_helpers import confirm_action
from plugins.studio.project_editor.pipeline_store import PipelineStore
from plugins.studio.project_editor.project_graph_view import ProjectGraphView

_ADD_NEW_PROJECT = "__add_new_project__"


class ProjectEditorPage(QWidget):
    """Top-level section page (see plugin.py's register(api)): a top bar
    (project picker + Add New Project + Rename/Delete Project + Add Repo)
    and a QGraphicsView node graph below it (1 node = 1 repo,
    ProjectGraphView), full width. Repo settings (Project Status, Browser,
    Local Repository, Enable Plugin, and any plugin's own CATEGORY_REPO
    tab) are no longer a permanent right panel here — as of 2026-07-15
    they're a popup (RepoSettingsPanel wrapped in RepoSettingsDialog,
    repo_settings_panel.py) opened via a node's right-click context menu
    ("Repository Setting...", see project_graph_view.py). Implements the
    standard set_repo() page protocol purely to keep the graph's active-
    node highlight in sync — this page never receives commands to change
    the active repo, only notifications that it already changed (a node
    click here, or an action on another section)."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        program_store: ProgramStore,
        addon_store: AddonMetadataStore,
        addon_catalog: list[DiscoveredPlugin],
        pipeline_store: PipelineStore,
        settings_tab_registry: SettingsTabRegistry,
    ):
        super().__init__(parent)
        self.store = store
        self._last_project_id: str | None = None

        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._on_project_combo_changed)

        rename_project_btn = QPushButton("Rename Project...")
        rename_project_btn.clicked.connect(self._on_rename_project)
        delete_project_btn = QPushButton("Delete Project...")
        delete_project_btn.clicked.connect(self._on_delete_project)
        add_repo_btn = QPushButton("Add Repo")
        add_repo_btn.clicked.connect(self._on_add_repo)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.project_combo, stretch=1)
        top_bar.addWidget(rename_project_btn)
        top_bar.addWidget(delete_project_btn)
        top_bar.addWidget(add_repo_btn)

        self.graph_view = ProjectGraphView(
            store=store,
            local_config_store=local_config_store,
            program_store=program_store,
            addon_store=addon_store,
            addon_catalog=addon_catalog,
            pipeline_store=pipeline_store,
            settings_tab_registry=settings_tab_registry,
        )

        layout = QVBoxLayout(self)
        layout.addLayout(top_bar)
        layout.addWidget(self.graph_view, stretch=1)

        self._refresh_project_combo()

    # -- SectionHost wiring (see plugin.py's _wire) ----------------------

    def bind_set_active_repo(self, callback: Callable[[str, str], None]) -> None:
        self.graph_view.bind_set_active_repo(callback)

    # -- page protocol (see interface/section_registry.py) ----------------

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self.graph_view.set_active_repo(project, repo)
        # Only reload the graph when the active repo's project actually
        # differs from what's already loaded — set_repo() fires on every
        # active-repo change, including a node click inside the very
        # project already showing. Reloading unconditionally would destroy
        # every RepoNodeItem in the scene (ProjectGraphView.load_project's
        # scene.clear()) while one of them is still mid-mousePressEvent,
        # crashing with "Internal C++ object already deleted" once that
        # handler resumes.
        if project is not None and project.id != self._last_project_id:
            self._select_project_in_combo(project.id)

    # -- project dropdown --------------------------------------------------

    def _refresh_project_combo(self, *, select_project_id: str | None = None) -> None:
        blocked = self.project_combo.blockSignals(True)
        self.project_combo.clear()
        for project in self.store.list_projects():
            self.project_combo.addItem(project.name, project.id)
        self.project_combo.addItem("Add New Project...", _ADD_NEW_PROJECT)
        self.project_combo.blockSignals(blocked)

        target_id = select_project_id or self._last_project_id
        if target_id is not None and self.project_combo.findData(target_id) >= 0:
            self._set_combo_index_silently(target_id)
        elif self.project_combo.count() > 1:
            self._set_combo_index_silently(self.project_combo.itemData(0))
        self._load_current_project()

    def _set_combo_index_silently(self, project_id: str) -> None:
        index = self.project_combo.findData(project_id)
        if index >= 0:
            blocked = self.project_combo.blockSignals(True)
            self.project_combo.setCurrentIndex(index)
            self.project_combo.blockSignals(blocked)

    def _select_project_in_combo(self, project_id: str) -> None:
        self._set_combo_index_silently(project_id)
        self._load_current_project()

    def _current_project_id(self) -> str | None:
        data = self.project_combo.currentData()
        return data if data and data != _ADD_NEW_PROJECT else None

    def _load_current_project(self) -> None:
        project_id = self._current_project_id()
        self._last_project_id = project_id
        self.graph_view.load_project(project_id)

    def _on_project_combo_changed(self, index: int) -> None:
        if self.project_combo.itemData(index) == _ADD_NEW_PROJECT:
            self._on_add_new_project()
            return
        self._load_current_project()

    def _on_add_new_project(self) -> None:
        dialog = ProjectDialog(self)
        if dialog.exec():
            try:
                project = self.store.add_project(dialog.name())
            except UkoreHubError as exc:
                QMessageBox.warning(self, "Add Project", str(exc))
                self._refresh_project_combo(select_project_id=self._last_project_id)
                return
            self._refresh_project_combo(select_project_id=project.id)
        else:
            self._refresh_project_combo(select_project_id=self._last_project_id)

    def _on_rename_project(self) -> None:
        project_id = self._current_project_id()
        if project_id is None:
            QMessageBox.information(self, "Rename Project", "Select a project first.")
            return
        project = self.store.get_project(project_id)
        dialog = ProjectDialog(self, name=project.name)
        if not dialog.exec():
            return
        try:
            self.store.rename_project(project_id, dialog.name())
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Rename Project", str(exc))
            return
        self._refresh_project_combo(select_project_id=project_id)

    def _on_delete_project(self) -> None:
        project_id = self._current_project_id()
        if project_id is None:
            QMessageBox.information(self, "Delete Project", "Select a project first.")
            return
        project = self.store.get_project(project_id)
        if not confirm_action(
            self,
            "Delete Project",
            f"Delete project '{project.name}' and ALL its repos from the registry for EVERYONE at the studio?\n\n"
            "This removes them from the shared registry immediately and cannot be undone.",
        ):
            return
        self.store.delete_project(project_id)
        self._last_project_id = None
        self._refresh_project_combo()

    def _on_add_repo(self) -> None:
        self.graph_view.add_repo()
