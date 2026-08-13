from __future__ import annotations

from plugin_api import CATEGORY_DEVELOPER, SettingsTabSpec
from plugins.core.CloudDataAdmin.cloud_data_admin_page import CloudDataAdminPage

PLUGIN_ID = "cloud_data_admin"


def register(api) -> None:
    api.register_settings_tab(
        SettingsTabSpec(
            key=PLUGIN_ID,
            label="Cloud Data",
            order=40,
            page_factory=lambda: CloudDataAdminPage(api=api),
            category=CATEGORY_DEVELOPER,
        )
    )
