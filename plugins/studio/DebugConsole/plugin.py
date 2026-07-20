from __future__ import annotations

from interface.section_registry import SectionSpec
from plugins.studio.DebugConsole.debug_console_page import DebugConsolePage

SECTION_KEY = "debug_console"


def register(api) -> None:
    page = DebugConsolePage()
    api.register_section(
        SectionSpec(
            key=SECTION_KEY,
            label="Debug Console",
            order=900,
            page_factory=lambda: page,
        )
    )
