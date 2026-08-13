from __future__ import annotations

from PySide6.QtWidgets import QStyle

from plugin_api import SectionSpec
from plugins.core.DebugConsole.debug_console_page import DebugConsolePage

SECTION_KEY = "debug_console"


def register(api) -> None:
    page = DebugConsolePage(debug_bus=api.debug_bus)
    api.register_section(
        SectionSpec(
            key=SECTION_KEY,
            label="Debug Console",
            order=900,
            standard_icon=QStyle.SP_MessageBoxInformation,
            page_factory=lambda: page,
        )
    )
