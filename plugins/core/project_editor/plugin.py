from __future__ import annotations

from plugin_api import CATEGORY_PROJECT, CATEGORY_REPO, SectionSpec, SettingsTabSpec, UICommandService
from plugins.core.project_editor.custom_paths_settings_page import CustomPathsSettingsPage
from plugins.core.project_editor.pipeline_store import PipelineStore, migrate_legacy_data
from plugins.core.project_editor.project_editor_page import ProjectEditorPage
from plugins.core.project_editor.project_settings_page import ProjectSettingsPage
from PySide6.QtWidgets import QStyle

PLUGIN_ID = "project_editor"
SECTION_KEY = PLUGIN_ID
PROJECT_SETTINGS_KEY = "project_editor_project"
CUSTOM_PATHS_SETTINGS_KEY = "project_editor_custom_paths"


def _wire(page: ProjectEditorPage, host: UICommandService) -> None:
    page.bind_set_active_repo(host.set_active_repo)
    page.bind_switch_project(host.switch_project)
    page.bind_open_settings_tab(host.open_settings_tab)


def register(api) -> None:
    migrate_legacy_data(api)
    pipeline_store = PipelineStore(api.metadata)
    page = ProjectEditorPage(
        store=api.metadata,
        local_config_store=api.local_config,
        pipeline_store=pipeline_store,
        git_service=api.git,
    )
    api.register_section(
        SectionSpec(
            key=SECTION_KEY,
            label="Project Editor",
            order=5,
            page_factory=lambda: page,
            wire=_wire,
            standard_icon=QStyle.SP_FileDialogListView,
        )
    )
    api.register_settings_tab(
        SettingsTabSpec(
            key=PROJECT_SETTINGS_KEY,
            label="Project",
            order=0,
            page_factory=lambda: ProjectSettingsPage(
                store=api.metadata,
                get_current_project_id=page.current_project_id,
                add_repo=page.add_repo,
                on_switch_project=page.switch_project,
            ),
            on_activated=lambda widget: widget.refresh(),
            category=CATEGORY_PROJECT,
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
