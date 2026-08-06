from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QVBoxLayout, QWidget

from core.models import Project, Repo
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore
from interface.settings_tab_registry import SettingsTabRegistry
from plugins.core.project_editor.pipeline_store import PipelineStore
from plugins.core.project_editor.project_graph_view import ProjectGraphView


class ProjectEditorPage(QWidget):
    """Top-level section page (see plugin.py's register(api)): no top bar
    at all as of 2026-08-03 — the project picker + Rename/Delete Project
    buttons (moved 2026-08-03 earlier) and the Add Repo button (moved
    2026-08-03) all now live in Setting > Project, see
    project_settings_page.py, per the user's own request to declutter this
    always-visible bar down to nothing but the graph itself. Just a
    QGraphicsView node graph (1 node = 1 repo, ProjectGraphView), full
    width/height. Repo settings (Browser, Local Repository,
    Requirements & Plugins, and any plugin's own CATEGORY_REPO tab) are also
    not a permanent right panel here — as of 2026-07-15 they're a popup
    (RepoSettingsPanel wrapped in RepoSettingsDialog, repo_settings_panel.py)
    opened via a node's right-click context menu ("Repository Setting...",
    see project_graph_view.py). Implements the standard set_repo() page
    protocol purely to keep the graph's active-node highlight (and which
    project it's showing) in sync — this page never receives commands to
    change the active repo, only notifications that it already changed (a
    node click here, or an action on another section).

    current_project_id()/set_current_project()/add_repo() are this page's
    own single source of truth/entry points for "which project is the
    graph currently showing" and "add a repo to it" — plugin.py binds these
    to project_settings_page.py's get_current_project_id/
    set_current_project_id/add_repo callbacks, so a freshly-constructed
    ProjectSettingsPage always reads/writes/acts through to this persistent
    page rather than holding that state itself."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        program_store: ProgramStore,
        pipeline_store: PipelineStore,
        settings_tab_registry: SettingsTabRegistry,
    ):
        super().__init__(parent)
        self.store = store
        self._last_project_id: str | None = None

        self.graph_view = ProjectGraphView(
            store=store,
            local_config_store=local_config_store,
            program_store=program_store,
            pipeline_store=pipeline_store,
            settings_tab_registry=settings_tab_registry,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.graph_view, stretch=1)

        # Default to the first project in the registry (if any) — there's
        # no dropdown here anymore to drive this; Setting > Project
        # (project_settings_page.py) reads this same current_project_id()
        # on its own first refresh() and only changes it from then on via
        # set_current_project() below.
        projects = self.store.list_projects()
        self.set_current_project(projects[0].id if projects else None)

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
            self.set_current_project(project.id)

    # -- current project (see project_settings_page.py's callbacks) -------

    def current_project_id(self) -> str | None:
        return self._last_project_id

    def set_current_project(self, project_id: str | None) -> None:
        self._last_project_id = project_id
        self.graph_view.load_project(project_id)

    def add_repo(self) -> None:
        self.graph_view.add_repo()
