from __future__ import annotations

from interface.settings_tab_registry import CATEGORY_DEVELOPER, SettingsTabSpec
from plugins.core.ExternalPlugins.catalog_store import ExternalPluginCatalog
from plugins.core.ExternalPlugins.external_plugins_page import ExternalPluginsPage

PLUGIN_ID = "external_plugins"


def register(api) -> None:
    # A fresh ExternalPluginCatalog/page per open, same as every other
    # Settings tab's page_factory (see interface/settings/settings_view.py's
    # SettingsView docstring) — SettingsDialog is reconstructed from scratch
    # on every open, so there's no long-lived page to reuse or clean up.
    catalog = ExternalPluginCatalog(api.plugin_config_store(PLUGIN_ID, shared=True))
    api.register_settings_tab(
        SettingsTabSpec(
            key=PLUGIN_ID,
            label="External Plugins",
            # After the built-in Developer tabs (Plugins is order=30, the
            # highest today — see interface/builtin_settings_tabs.py).
            order=40,
            page_factory=lambda: ExternalPluginsPage(
                git_service=api.git,
                plugins_root=api.app_root / "cache" / "plugins",
                catalog=catalog,
                plugin_catalog=api.plugin_catalog,
            ),
            category=CATEGORY_DEVELOPER,
        )
    )
