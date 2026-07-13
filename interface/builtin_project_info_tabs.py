from __future__ import annotations

from core.extensibility.loader import DiscoveredPlugin
from core.git_service import GitService
from core.store import LocalConfigStore, MetadataStore
from interface.pages.project_info_main_tab import ProjectInfoMainTab
from interface.pages.repo_addon_tab import RepoAddonTab
from interface.project_info_tab_registry import ProjectInfoTabRegistry, ProjectInfoTabSpec
from interface.repo_addon_panel_registry import RepoAddonPanelRegistry

MAIN = "main"
REPO_ADDON = "repo_addon"


def register_builtin_project_info_tabs(
    registry: ProjectInfoTabRegistry,
    *,
    store: MetadataStore,
    local_config_store: LocalConfigStore,
    git_service: GitService,
    repo_addon_panel_registry: RepoAddonPanelRegistry,
    addon_catalog: list[DiscoveredPlugin],
) -> None:
    registry.register(
        ProjectInfoTabSpec(
            key=MAIN,
            label="Main",
            order=0,
            page_factory=lambda: ProjectInfoMainTab(
                store=store, local_config_store=local_config_store, git_service=git_service
            ),
        )
    )
    registry.register(
        ProjectInfoTabSpec(
            key=REPO_ADDON,
            label="Repo Add-on",
            order=10,
            page_factory=lambda: RepoAddonTab(
                repo_addon_panel_registry=repo_addon_panel_registry, addon_catalog=addon_catalog
            ),
        )
    )
