from __future__ import annotations

from core.extensibility.loader import DiscoveredPlugin, PluginLoadFailure
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
from interface.browser_links.browser_links_settings_page import BrowserLinksSettingsPage
from interface.repo_settings.enable_plugin_page import EnablePluginPage
from interface.repo_settings.local_repository_page import LocalRepositoryPage
from interface.settings.common_settings_page import CommonSettingsPage
from interface.settings.github_oauth_settings_page import GithubOAuthSettingsPage
from interface.settings.plugin_catalog_page import PluginCatalogPage
from interface.settings.program_database_page import ProgramDatabasePage
from interface.settings_tab_registry import (
    CATEGORY_DEVELOPER,
    CATEGORY_GENERAL,
    CATEGORY_REPO,
    SettingsTabRegistry,
    SettingsTabSpec,
)

COMMON = "common"
PROGRAM_DATABASE = "program_database"
PLUGINS = "plugins"
GITHUB_OAUTH = "github_oauth"
BROWSER_LINKS = "browser_links"
LOCAL_REPOSITORY = "local_repository"
ENABLE_PLUGIN = "enable_plugin"

PLUGINS_DESCRIPTION = (
    "Plugins are UkoreHub's own sub-systems, discovered here app-wide. "
    "To turn one off for a specific repo, see Settings > (repo) > Enable Plugin."
)


def register_builtin_settings_tabs(
    registry: SettingsTabRegistry,
    *,
    store: MetadataStore,
    local_config_store: LocalConfigStore,
    system_config_store: SystemConfigStore,
    program_store: ProgramStore,
    plugin_catalog: list[DiscoveredPlugin],
    plugin_load_failures: list[PluginLoadFailure],
) -> None:
    """Registers the built-in settings tabs the same way a plugin would.
    Each page_factory constructs a *fresh* widget on every call (not a
    reused singleton) so re-opening the Settings dialog still gets clean
    page state, matching the pre-registry behavior where SettingsDialog
    built new pages on every open. Every page persists its own changes
    immediately — no on_save/on_cancel polling anymore."""

    # Shared on_activated for every tab whose only refresh need is
    # "call refresh() if this page has one" — BrowserLinksSettingsPage,
    # LocalRepositoryPage, EnablePluginPage all just want that, so one
    # duck-typed callback replaces a 1:1 wrapper per page type.
    def _trigger_refresh(widget) -> None:
        refresh = getattr(widget, "refresh", None)
        if callable(refresh):
            refresh()

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
            key=BROWSER_LINKS,
            label="Browser",
            order=20,
            page_factory=lambda: BrowserLinksSettingsPage(store=store, local_config_store=local_config_store),
            on_activated=_trigger_refresh,
            category=CATEGORY_REPO,
        )
    )
    registry.register(
        SettingsTabSpec(
            key=LOCAL_REPOSITORY,
            label="Local Repository",
            order=25,
            page_factory=lambda: LocalRepositoryPage(store=store, local_config_store=local_config_store),
            on_activated=_trigger_refresh,
            category=CATEGORY_REPO,
        )
    )
    registry.register(
        SettingsTabSpec(
            key=ENABLE_PLUGIN,
            label="Enable Plugin",
            order=27,
            page_factory=lambda: EnablePluginPage(
                store=store, local_config_store=local_config_store, plugin_catalog=plugin_catalog
            ),
            on_activated=_trigger_refresh,
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
