from __future__ import annotations

from core.addon_store import AddonMetadataStore
from core.extensibility.file_opener import FileOpenerRegistry
from core.extensibility.loader import DiscoveredPlugin
from core.git_service import GitService
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore
from interface.pages.project_info_page import ProjectInfoPage
from interface.pages.repo_about_page import RepoAboutPage
from interface.pages.repo_browser_page import RepoBrowserPage
from interface.pages.repo_git_status_page import RepoGitStatusPage
from interface.project_info_tab_registry import ProjectInfoTabRegistry
from interface.section_registry import SectionRegistry, SectionSpec

# Same string values as the old SectionKey(str, Enum) members, so anything
# persisted under these strings (e.g. nothing currently is, but this keeps
# the door open) stays stable across the migration.
PROJECT_INFO = "project_info"
REPO_BROWSER = "repo_browser"
REPO_GIT_STATUS = "repo_git_status"
REPO_ABOUT = "repo_about"


def register_builtin_sections(
    registry: SectionRegistry,
    *,
    store: MetadataStore,
    local_config_store: LocalConfigStore,
    git_service: GitService,
    program_store: ProgramStore,
    addon_store: AddonMetadataStore,
    project_info_tab_registry: ProjectInfoTabRegistry,
    file_opener_registry: FileOpenerRegistry,
    addon_catalog: list[DiscoveredPlugin],
) -> dict[str, object]:
    """Constructs the built-in pages and registers them into `registry`
    exactly like a plugin would register its own — orders are spaced out
    (0/10/20/30) to leave room for plugins to insert sections in between.
    Returns {key: page instance} for the handful of things main_window.py
    still needs direct references to (RepoGitStatusPage's sync signals, and
    RepoBrowserPage's commit-history worker for shutdown cleanup).

    PROJECT_INFO is deliberately NOT built eagerly here (unlike the other 3)
    — its page_factory constructs on MainWindow's first (and only) call,
    which happens after apply_plugins() has run, so any plugin-registered
    project_info_tab_registry entries are visible by construction time."""
    repo_browser_page = RepoBrowserPage(
        store=store,
        local_config_store=local_config_store,
        git_service=git_service,
        file_opener_registry=file_opener_registry,
    )
    repo_git_status_page = RepoGitStatusPage(
        store=store, local_config_store=local_config_store, git_service=git_service
    )
    repo_about_page = RepoAboutPage(
        store=store,
        local_config_store=local_config_store,
        program_store=program_store,
        addon_store=addon_store,
        git_service=git_service,
        addon_catalog=addon_catalog,
    )

    pages: dict[str, object] = {
        REPO_BROWSER: repo_browser_page,
        REPO_GIT_STATUS: repo_git_status_page,
        REPO_ABOUT: repo_about_page,
    }

    registry.register(
        SectionSpec(
            key=PROJECT_INFO,
            label="Repo",
            order=0,
            page_factory=lambda: ProjectInfoPage(
                store=store,
                local_config_store=local_config_store,
                git_service=git_service,
                project_info_tab_registry=project_info_tab_registry,
            ),
        )
    )
    registry.register(
        SectionSpec(
            key=REPO_BROWSER,
            label="Explorer",
            order=10,
            page_factory=lambda: repo_browser_page,
            background_threads=lambda page: [page.browser.commit_panel._worker],
            standalone=True,
        )
    )
    registry.register(
        SectionSpec(
            key=REPO_GIT_STATUS,
            label="Submit",
            order=20,
            page_factory=lambda: repo_git_status_page,
            background_threads=lambda page: [
                page._git_worker,
                page._status_worker,
                page._stream_worker,
                page._commit_log_worker,
            ],
            standalone=True,
        )
    )
    registry.register(SectionSpec(key=REPO_ABOUT, label="About", order=30, page_factory=lambda: repo_about_page))

    return pages
