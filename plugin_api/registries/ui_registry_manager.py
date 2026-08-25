from __future__ import annotations

from dataclasses import dataclass

from core_api import FileOpenerRegistry
from plugin_api.registries.notification_registry import NotificationRegistry
from plugin_api.registries.program_launch_registry import ProgramLaunchRegistry
from plugin_api.registries.section_registry import SectionRegistry
from plugin_api.registries.settings_tab_registry import SettingsTabRegistry
from plugin_api.registries.sidebar_footer_action_registry import SidebarFooterActionRegistry


@dataclass(frozen=True)
class UIRegistryManager:
    """Bundles every open, plugin-facing UI registry into one object —
    launcher.py constructs a single instance and threads it into both
    PluginAPI and MainWindow, instead of five separate constructor
    parameters each had to repeat. Purely a construction/wiring
    simplification: each registry keeps its own type, its own
    register()/ordered() surface, and its own call sites everywhere else
    (PluginAPI.register_section still writes to registries.sections, exactly
    as it wrote to a bare section_registry parameter before) — nothing
    about how a plugin registers anything changes."""

    sections: SectionRegistry
    settings_tabs: SettingsTabRegistry
    file_openers: FileOpenerRegistry
    program_launchers: ProgramLaunchRegistry
    sidebar_footer_actions: SidebarFooterActionRegistry
    notifications: NotificationRegistry
