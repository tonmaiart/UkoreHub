from __future__ import annotations

from interface.section_registry import SectionSpec
from interface.settings_tab_registry import CATEGORY_REPO, SettingsTabSpec
from plugins.studio.explorer.explorer_settings_page import ExplorerSettingsPage
from plugins.studio.explorer.repo_browser_page import RepoBrowserPage

SECTION_KEY = "repo_browser"
SETTINGS_KEY = "explorer_settings"


def register(api) -> None:
    page = RepoBrowserPage(
        local_config_store=api.local_config,
        git_service=api.git,
        file_opener_registry=api.file_opener_registry,
    )
    icons_dir = api.app_root / "data" / "icons"
    api.register_section(
        SectionSpec(
            key=SECTION_KEY,
            label="Explorer",
            order=10,
            page_factory=lambda: page,
            background_threads=lambda p: [p.browser.commit_panel._worker],
            icon_path=icons_dir / "icons8-folder-50.png",
        )
    )

    # Convention-only string match with plugins/studio/pipeline_architect/plugin.py's
    # own PLUGIN_ID — both resolve to the same
    # data/plugins/studio/pipeline_architect.json via PluginConfigStore, no
    # coupling API needed (see that plugin's README "Reading pipeline data
    # from another plugin" section, the pattern this follows).
    pipeline_config_store = api.plugin_config_store("pipeline_architect", shared=True)
    api.register_settings_tab(
        SettingsTabSpec(
            key=SETTINGS_KEY,
            label="Explorer",
            order=26,
            page_factory=lambda: ExplorerSettingsPage(
                store=api.metadata,
                local_config_store=api.local_config,
                pipeline_config_store=pipeline_config_store,
            ),
            on_activated=lambda widget: widget.refresh(),
            category=CATEGORY_REPO,
        )
    )
