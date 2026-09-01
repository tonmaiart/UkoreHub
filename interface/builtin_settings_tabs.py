from __future__ import annotations

from core_api import DiscoveredPlugin, LocalConfigStore, PluginLoadFailure, SystemConfigStore
from interface.settings.common_settings_page import CommonSettingsPage
from interface.settings.github_oauth_settings_page import GithubOAuthSettingsPage
from interface.settings.plugin_catalog_page import PluginCatalogPage
from plugin_api import (
    CATEGORY_DEVELOPER,
    CATEGORY_GENERAL,
    SettingsTabRegistry,
    SettingsTabSpec,
)

COMMON = "common"
PLUGINS = "plugins"
GITHUB_OAUTH = "github_oauth"

PLUGINS_DESCRIPTION = (
    "Plugins are UkoreHub's own sub-systems, discovered here app-wide. "
    "To opt a repo into an Internal or External one, see "
    "Settings > Project > Repository Settings — Core plugins are always on."
)


def register_builtin_settings_tabs(
    registry: SettingsTabRegistry,
    *,
    local_config_store: LocalConfigStore,
    system_config_store: SystemConfigStore,
    plugin_catalog: list[DiscoveredPlugin],
    plugin_load_failures: list[PluginLoadFailure],
) -> None:
    """Registers the built-in settings tabs the same way a plugin would.
    Each page_factory constructs a *fresh* widget on every call (not a
    reused singleton) so re-opening the Settings dialog still gets clean
    page state, matching the pre-registry behavior where SettingsDialog
    built new pages on every open. Every page persists its own changes
    immediately — no on_save/on_cancel polling anymore.

    Program Database and Requirements & Plugins used to be registered here
    too — both moved to plugins/core/project_editor/'s "Project Database"
    and "Repository Settings" tabs as part of the External Plugin Manager
    merge (see that plugin's project_database_page.py/repo_settings_page.py),
    which is why git_service/plugins_root are no longer parameters here.
    Local Repository (the last CATEGORY_REPO builtin tab, `store` was only
    needed for it) was removed 2026-09-01 as redundant with
    project_editor_page.py's own per-repo Unclone button — see that
    plugin's doc — which is why `store` isn't a parameter here anymore
    either; every remaining tab here is CATEGORY_GENERAL/CATEGORY_DEVELOPER."""

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
            key=GITHUB_OAUTH,
            label="GitHub OAuth Client ID",
            order=0,
            page_factory=lambda: GithubOAuthSettingsPage(system_config_store=system_config_store),
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
