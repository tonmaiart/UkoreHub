from __future__ import annotations

from interface.section_registry import SectionSpec
from plugins.core.DebugConsole.debug_console_page import DebugConsolePage

SECTION_KEY = "debug_console"


def register(api) -> None:
    icons_dir = api.app_root / "data" / "icons"
    page = DebugConsolePage()
    api.register_section(
        SectionSpec(
            key=SECTION_KEY,
            label="Debug Console",
            order=900,
            icon_path=icons_dir / "icons8-debug-50.png",
            page_factory=lambda: page,
        )
    )
