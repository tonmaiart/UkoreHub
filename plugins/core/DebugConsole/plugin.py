from __future__ import annotations

from PySide6.QtWidgets import QStyle

from plugin_api import SectionSpec
from plugins.core.DebugConsole.debug_console_page import DebugConsolePage

SECTION_KEY = "debug_console"


def register(api) -> None:
    if api.debug_log_handler is None:
        # No QApplication/launcher.py logging wiring (e.g. a bare
        # UkoreCore() test construction) — nothing for this page to show.
        return
    page = DebugConsolePage(handler=api.debug_log_handler)
    api.register_section(
        SectionSpec(
            key=SECTION_KEY,
            label="Debug Console",
            order=900,
            standard_icon=QStyle.SP_MessageBoxInformation,
            page_factory=lambda: page,
        )
    )
