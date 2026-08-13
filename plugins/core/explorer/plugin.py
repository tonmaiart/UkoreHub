from __future__ import annotations

from PySide6.QtWidgets import QStyle

from plugin_api import SectionSpec
from plugins.core.explorer.repo_browser_page import RepoBrowserPage

SECTION_KEY = "repo_browser"


def register(api) -> None:
    page = RepoBrowserPage(
        local_config_store=api.local_config,
        git_service=api.git,
        file_opener_registry=api.file_opener_registry,
        cache_dir=api.cache_dir,
        api=api,
    )
    api.debug_bus.register_source("Explorer")
    api.register_section(
        SectionSpec(
            key=SECTION_KEY,
            label="Explorer",
            order=10,
            page_factory=lambda: page,
            background_threads=lambda p: [p.browser.commit_panel._worker],
            standard_icon=QStyle.SP_DirIcon,
        )
    )