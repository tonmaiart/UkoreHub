from __future__ import annotations

from pathlib import Path

from core.addon_store import AddonMetadataStore
from core.extensibility.file_opener import FileOpenerRegistry
from core.extensibility.loader import DiscoveredPlugin
from core.git_service import GitService
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore
from interface.about.repo_about_page import RepoAboutPage
from interface.explorer.repo_browser_page import RepoBrowserPage
from interface.submit.repo_git_status_page import RepoGitStatusPage
from interface.repo_addon_panel_registry import RepoAddonPanelRegistry
from interface.section_registry import SectionRegistry, SectionSpec

# Same string values as the old SectionKey(str, Enum) members, so anything
# persisted under these strings (e.g. nothing currently is, but this keeps
# the door open) stays stable across the migration.
REPO_BROWSER = "repo_browser"
REPO_GIT_STATUS = "repo_git_status"
REPO_ABOUT = "repo_about"

_ICONS_DIR = Path(__file__).resolve().parent.parent / "data" / "icons"


def register_builtin_sections(
    registry: SectionRegistry,
    *,
    store: MetadataStore,
    local_config_store: LocalConfigStore,
    git_service: GitService,
    program_store: ProgramStore,
    addon_store: AddonMetadataStore,
    repo_addon_panel_registry: RepoAddonPanelRegistry,
    file_opener_registry: FileOpenerRegistry,
    addon_catalog: list[DiscoveredPlugin],
) -> dict[str, object]:
    """Constructs the built-in pages and registers them into `registry`
    exactly like a plugin would register its own — orders are spaced out
    (10/20/30) to leave room for plugins to insert sections in between.
    Returns {key: page instance} for the handful of things main_window.py
    still needs direct references to (RepoGitStatusPage's sync signals, and
    RepoBrowserPage's commit-history worker for shutdown cleanup)."""
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
        repo_addon_panel_registry=repo_addon_panel_registry,
    )

    pages: dict[str, object] = {
        REPO_BROWSER: repo_browser_page,
        REPO_GIT_STATUS: repo_git_status_page,
        REPO_ABOUT: repo_about_page,
    }

    registry.register(
        SectionSpec(
            key=REPO_BROWSER,
            label="Explorer",
            order=10,
            page_factory=lambda: repo_browser_page,
            background_threads=lambda page: [page.browser.commit_panel._worker],
            icon_path=_ICONS_DIR / "icons8-folder-50.png",
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
            icon_path=_ICONS_DIR / "icons8-submit-50.png",
        )
    )
    registry.register(
        SectionSpec(
            key=REPO_ABOUT,
            label="About",
            order=30,
            page_factory=lambda: repo_about_page,
            icon_path=_ICONS_DIR / "icons8-about-32.png",
        )
    )

    return pages
