from __future__ import annotations

from interface.settings_tab_registry import CATEGORY_DEVELOPER, SettingsTabSpec
from plugins.studio.pipeline_architect.editor_page import ProjectDataEditorPage
from plugins.studio.pipeline_architect.pipeline_store import PipelineStore

PLUGIN_ID = "pipeline_architect"


def register(api) -> None:
    pipeline_store = PipelineStore(api.plugin_config_store(PLUGIN_ID, shared=True))
    api.register_settings_tab(
        SettingsTabSpec(
            key=PLUGIN_ID,
            label="Project Data Editor",
            order=10,
            page_factory=lambda: ProjectDataEditorPage(
                store=api.metadata,
                local_config_store=api.local_config,
                program_store=api.programs,
                addon_store=api.addon_store,
                addon_catalog=api.addon_catalog,
                pipeline_store=pipeline_store,
            ),
            category=CATEGORY_DEVELOPER,
        )
    )
