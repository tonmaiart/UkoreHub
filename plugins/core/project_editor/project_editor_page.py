from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QVBoxLayout, QWidget

from plugin_api import GitService, LocalConfigStore, MetadataStore, Project, Repo
from plugins.core.project_editor.pipeline_store import PipelineStore
from plugins.core.project_editor.project_graph_view import ProjectGraphView


class ProjectEditorPage(QWidget):
    """Top-level section page (see plugin.py's register(api)): no top bar
    at all as of 2026-08-03 — the project picker + Rename/Delete Project
    buttons (moved 2026-08-03 earlier) and the Add Repo button (moved
    2026-08-03) all moved to Setting > Project, see project_settings_page.py,
    per the user's own request to declutter this always-visible bar down to
    nothing but the graph itself (the project picker there was itself later
    removed entirely — see that file's own docstring). Just a
    QGraphicsView node graph (1 node = 1 repo, ProjectGraphView), full
    width/height. Implements the standard set_repo() page protocol purely
    to keep the graph's active-node highlight (and which project it's
    showing) in sync — this page never receives commands to change the
    active repo, only notifications that it already changed (a node click
    here, or an action on another section).

    Repo settings (Browser, Local Repository, Requirements & Plugins, and
    any plugin's own CATEGORY_REPO tab) render generically in the main
    Settings dialog's Repo Setting (Dev) category (see
    interface/settings/settings_view.py). A repo node's right-click
    "Repository Setting..." opens that same dialog via
    UICommandService.open_settings_tab (bind_open_settings_tab below) rather
    than a plugin-owned popup — from 2026-07-15 through this refactor they
    briefly lived in their own popup instead (RepoSettingsPanel/
    RepoSettingsDialog, repo_settings_panel.py, now retired) to avoid
    duplicating them in both Settings and here; the same reasoning now
    argues for a single dialog rather than a single popup, since both were
    only ever reading the same SettingsTabRegistry entries.

    current_project_id()/add_repo() are this page's own single source of
    truth/entry points for "which project the graph is showing" (fixed for
    the whole run, see __init__ below) and "add a repo to it" — plugin.py
    binds these to project_settings_page.py's get_current_project_id/
    add_repo callbacks, so a freshly-constructed ProjectSettingsPage always
    reads/acts through to this persistent page rather than holding that
    state itself. set_current_project() still exists as the one place that
    actually loads a project into the graph, but as of the single-project-
    per-session change nothing calls it with a project id other than the
    one launcher.py's gate already fixed — see switch_project() below for
    the only real way to view a different one."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        pipeline_store: PipelineStore,
        git_service: GitService,
    ):
        super().__init__(parent)
        self.store = store
        self._last_project_id: str | None = None
        self._switch_project_callback: Callable[[], None] | None = None

        self.graph_view = ProjectGraphView(
            store=store,
            local_config_store=local_config_store,
            pipeline_store=pipeline_store,
            git_service=git_service,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.graph_view, stretch=1)

        # Fixed to whichever project launcher.py's mandatory Project
        # Selector gate locked in for this run (local_config_store's
        # active_project_id, guaranteed to reference a real project by the
        # time plugins are constructed — see launcher.py) — there's no
        # dropdown here anymore that could show a different one; Setting >
        # Project (project_settings_page.py) reads this same
        # current_project_id() and can only trigger a full restart back
        # through that gate to view a different project at all (see
        # switch_project() below).
        self.set_current_project(local_config_store.active_project_id)

    # -- UICommandService wiring (see plugin.py's _wire) ----------------------

    def bind_set_active_repo(self, callback: Callable[[str, str], None]) -> None:
        self.graph_view.bind_set_active_repo(callback)

    def bind_open_settings_tab(self, callback: Callable[[str], None]) -> None:
        self.graph_view.bind_open_settings_tab(callback)

    def bind_switch_project(self, callback: Callable[[], None]) -> None:
        self._switch_project_callback = callback

    def switch_project(self) -> None:
        """Bound to project_settings_page.py's "Switch Project..." button —
        wraps UICommandService.switch_project (plugin_api/registries/section_registry.py),
        itself wrapping MainWindow._request_switch_project. Never changes
        current_project_id() in place; a real restart is the only way this
        app admits a different project."""
        if self._switch_project_callback is not None:
            self._switch_project_callback()

    # -- page protocol (see plugin_api/registries/section_registry.py) ----------------

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
