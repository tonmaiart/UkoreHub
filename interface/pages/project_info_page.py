from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from core.git_service import GitService
from core.models import Project, Repo
from core.store import LocalConfigStore, MetadataStore
from interface.project_info_tab_registry import ProjectInfoTabRegistry


class ProjectInfoPage(QWidget):
    """Thin QTabWidget shell over whatever's registered in
    `project_info_tab_registry` — the built-in "Main" tab plus any tabs a
    plugin has added via `PluginAPI.register_project_info_tab(...)`."""

    def __init__(
        self,
        parent=None,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        git_service: GitService,
        project_info_tab_registry: ProjectInfoTabRegistry,
    ):
        super().__init__(parent)
        self.tabs = QTabWidget()
        self._tab_widgets: dict[str, QWidget] = {}
        for spec in project_info_tab_registry.ordered():
            widget = spec.page_factory()
            self._tab_widgets[spec.key] = widget
            self.tabs.addTab(widget, spec.label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        for widget in self._tab_widgets.values():
            set_repo_fn = getattr(widget, "set_repo", None)
            if set_repo_fn is not None:
                set_repo_fn(project, repo, workspace_root)
