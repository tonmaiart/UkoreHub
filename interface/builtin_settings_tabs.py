from __future__ import annotations

from core.addon_store import AddonMetadataStore
from core.extensibility.loader import DiscoveredPlugin, PluginLoadFailure
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
from interface.settings_pages.addon_settings_page import AddonSettingsPage
from interface.settings_pages.color_theme_page import ColorThemePage
from interface.settings_pages.common_settings_page import CommonSettingsPage
from interface.settings_pages.plugin_catalog_page import PluginCatalogPage
from interface.settings_pages.program_database_page import ProgramDatabasePage
from interface.settings_pages.project_data_editor_page import ProjectDataEditorPage
from interface.settings_pages.project_status_page import ProjectStatusPage
from interface.settings_tab_registry import SettingsTabRegistry, SettingsTabSpec

COMMON = "common"
PROJECT_STATUS = "project_status"
PROJECT_DATA_EDITOR = "project_data_editor"
PROGRAM_DATABASE = "program_database"
COLOR_THEME = "color_theme"
PLUGINS = "plugins"
ADDONS = "addons"

PLUGINS_DESCRIPTION = (
    "Plugins are UkoreHub's own sub-systems — active for every project, "
    "not something you toggle per repo."
)
ADDONS_DESCRIPTION = (
    "Add-ons are extensions a repo opts into (enabled per repo in Project "
    "Data Editor). Enabling or disabling one affects everyone working on "
    "that repo — it's shared team data. Some add-ons or plugins may "
    "require others."
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
    addon_load_failures: list[PluginLoadFailure],
) -> None:
    """Registers the built-in settings tabs the same way a plugin would.
    Each page_factory constructs a *fresh* widget on every call (not a
    reused singleton) so re-opening the Settings dialog still gets clean
    page state, matching the pre-registry behavior where SettingsDialog
    built new pages on every open. Every page persists its own changes
    immediately — no on_save/on_cancel polling anymore."""

    def _activate_project_status(widget: ProjectStatusPage) -> None:
        widget.refresh()

    registry.register(
        SettingsTabSpec(
            key=COMMON,
            label="Common",
            order=0,
            page_factory=lambda: CommonSettingsPage(
                local_config_store=local_config_store, system_config_store=system_config_store
            ),
        )
    )
    registry.register(
        SettingsTabSpec(
            key=PROJECT_STATUS,
            label="Project Status",
            order=10,
            page_factory=lambda: ProjectStatusPage(store=store, local_config_store=local_config_store),
            on_activated=_activate_project_status,
        )
    )
    registry.register(
        SettingsTabSpec(
            key=PROJECT_DATA_EDITOR,
            label="Project Data Editor",
            order=20,
            page_factory=lambda: ProjectDataEditorPage(
                store=store,
                local_config_store=local_config_store,
                program_store=program_store,
                addon_store=addon_store,
                addon_catalog=addon_catalog,
            ),
        )
    )
    registry.register(
        SettingsTabSpec(
            key=PROGRAM_DATABASE,
            label="Program Database",
            order=30,
            page_factory=lambda: ProgramDatabasePage(program_store=program_store),
        )
    )
    registry.register(
        SettingsTabSpec(
            key=COLOR_THEME,
            label="Color Theme",
            order=40,
            page_factory=lambda: ColorThemePage(local_config_store=local_config_store),
        )
    )
    registry.register(
        SettingsTabSpec(
            key=PLUGINS,
            label="Plugins",
            order=50,
            page_factory=lambda: PluginCatalogPage(
                description=PLUGINS_DESCRIPTION, loaded=plugin_catalog, failures=plugin_load_failures
            ),
        )
    )
    registry.register(
        SettingsTabSpec(
            key=ADDONS,
            label="Add-ons",
            order=60,
            page_factory=lambda: AddonSettingsPage(
                description=ADDONS_DESCRIPTION,
                addon_catalog=addon_catalog,
                addon_load_failures=addon_load_failures,
                addon_store=addon_store,
                program_store=program_store,
            ),
        )
    )
