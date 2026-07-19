from __future__ import annotations

from interface.section_registry import SectionHost, SectionSpec
from interface.settings_tab_registry import CATEGORY_REPO, SettingsTabSpec
from plugins.studio.project_editor.custom_paths_settings_page import CustomPathsSettingsPage
from plugins.studio.project_editor.pipeline_store import PipelineStore
from plugins.studio.project_editor.project_editor_page import ProjectEditorPage

PLUGIN_ID = "project_editor"
SECTION_KEY = PLUGIN_ID
CUSTOM_PATHS_SETTINGS_KEY = "project_editor_custom_paths"


def _wire(page: ProjectEditorPage, host: SectionHost) -> None:
    page.bind_set_active_repo(host.set_active_repo)


def register(api) -> None:
    pipeline_store = PipelineStore(api.plugin_config_store(PLUGIN_ID, shared=True))
    page = ProjectEditorPage(
        store=api.metadata,
        local_config_store=api.local_config,
        program_store=api.programs,
        addon_store=api.addon_store,
        addon_catalog=api.addon_catalog,
        pipeline_store=pipeline_store,
        settings_tab_registry=api.settings_tab_registry,
    )
    api.register_section(
        SectionSpec(
            key=SECTION_KEY,
            label="Project Editor",
            order=5,
            page_factory=lambda: page,
            wire=_wire,
            # Always-visible docked panel, not a switchable sidebar row —
            # see interface/section_registry.py's SectionSpec.persistent.
            # register_section/wire/page_factory/background_threads all
            # still apply the same way; only Sidebar's SectionTabList row
            # and view_stack membership are skipped for a persistent
            # section (see MainWindow._build_main_ui).
            persistent=True,
        )
    )
    api.register_settings_tab(
        SettingsTabSpec(
            key=CUSTOM_PATHS_SETTINGS_KEY,
            label="Custom Paths",
            order=15,
            page_factory=lambda: CustomPathsSettingsPage(
                store=api.metadata,
                local_config_store=api.local_config,
                pipeline_store=pipeline_store,
            ),
            on_activated=lambda widget: widget.refresh(),
            category=CATEGORY_REPO,
        )
    )
