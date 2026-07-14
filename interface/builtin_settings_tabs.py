from __future__ import annotations

from core.addon_store import AddonMetadataStore
from core.extensibility.loader import DiscoveredPlugin, PluginLoadFailure
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
from interface.settings.browser_links_settings_page import BrowserLinksSettingsPage
from interface.settings.common_settings_page import CommonSettingsPage
from interface.settings.github_oauth_settings_page import GithubOAuthSettingsPage
from interface.settings.plugin_catalog_page import PluginCatalogPage
from interface.settings.program_database_page import ProgramDatabasePage
from interface.settings.project_data_editor_page import ProjectDataEditorPage
from interface.settings.project_status_page import ProjectStatusPage
from interface.settings_tab_registry import (
    CATEGORY_DEVELOPER,
    CATEGORY_GENERAL,
    CATEGORY_REPO,
    SettingsTabRegistry,
    SettingsTabSpec,
)

COMMON = "common"
PROJECT_STATUS = "project_status"
PROJECT_DATA_EDITOR = "project_data_editor"
PROGRAM_DATABASE = "program_database"
PLUGINS = "plugins"
GITHUB_OAUTH = "github_oauth"
BROWSER_LINKS = "browser_links"

PLUGINS_DESCRIPTION = (
    "Plugins are UkoreHub's own sub-systems — active for every project, "
    "not something you toggle per repo."
)


def register_builtin_settings_tabs(
    registry: SettingsTabRegistry,
    *,
    store: MetadataStore,
    local_config_store: LocalConfigStore,
    system_config_store: SystemConfigStore,
    program_store: ProgramStore,
    addon_store: AddonMetadataStore,
    addon_catalog: list[DiscoveredPlugin],
    plugin_catalog: list[DiscoveredPlugin],
    plugin_load_failures: list[PluginLoadFailure],
) -> None:
    """Registers the built-in settings tabs the same way a plugin would.
    Each page_factory constructs a *fresh* widget on every call (not a
    reused singleton) so re-opening the Settings dialog still gets clean
    page state, matching the pre-registry behavior where SettingsDialog
    built new pages on every open. Every page persists its own changes
    immediately — no on_save/on_cancel polling anymore."""

    def _activate_project_status(widget: ProjectStatusPage) -> None:
        widget.refresh()

    def _activate_browser_links(widget: BrowserLinksSettingsPage) -> None:
        widget.refresh()

    registry.register(
        SettingsTabSpec(
            key=COMMON,
            label="Common",
            order=0,
            page_factory=lambda: CommonSettingsPage(local_config_store=local_config_store),
            category=CATEGORY_GENERAL,
        )
    )
    registry.register(
        SettingsTabSpec(
            key=PROJECT_STATUS,
            label="Project Status",
            order=10,
            page_factory=lambda: ProjectStatusPage(store=store, local_config_store=local_config_store),
            on_activated=_activate_project_status,
            category=CATEGORY_REPO,
        )
    )
    registry.register(
        SettingsTabSpec(
            key=BROWSER_LINKS,
            label="Browser",
            order=20,
            page_factory=lambda: BrowserLinksSettingsPage(store=store, local_config_store=local_config_store),
            on_activated=_activate_browser_links,
            category=CATEGORY_REPO,
        )
    )
    registry.register(
        SettingsTabSpec(
            key=GITHUB_OAUTH,
            label="GitHub OAuth Client ID",
            order=0,
            page_factory=lambda: GithubOAuthSettingsPage(system_config_store=system_config_store),
            category=CATEGORY_DEVELOPER,
        )
    )
    registry.register(
        SettingsTabSpec(
            key=PROJECT_DATA_EDITOR,
            label="Project Data Editor",
            order=10,
            page_factory=lambda: ProjectDataEditorPage(
                store=store,
                local_config_store=local_config_store,
                program_store=program_store,
                addon_store=addon_store,
                addon_catalog=addon_catalog,
            ),
            category=CATEGORY_DEVELOPER,
        )
    )
    registry.register(
        SettingsTabSpec(
            key=PROGRAM_DATABASE,
            label="Program Database",
            order=20,
            page_factory=lambda: ProgramDatabasePage(program_store=program_store),
            category=CATEGORY_DEVELOPER,
        )
    )
    registry.register(
        SettingsTabSpec(
            key=PLUGINS,
            label="Plugins",
            order=30,
            page_factory=lambda: PluginCatalogPage(
                description=PLUGINS_DESCRIPTION, loaded=plugin_catalog, failures=plugin_load_failures
            ),
            category=CATEGORY_DEVELOPER,
        )
    )
