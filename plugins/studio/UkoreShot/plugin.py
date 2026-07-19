from __future__ import annotations

from interface.section_registry import SectionSpec
from interface.settings_tab_registry import CATEGORY_REPO, SettingsTabSpec
from plugins.studio.UkoreShot.repo_video_settings_page import RepoVideoSettingsPage
from plugins.studio.UkoreShot.video_library_page import UkoreShotPage

PLUGIN_ID = "ukore_shot"


def register(api) -> None:
    # A normal (non-persistent) section — main_window.py's
    # _apply_plugin_visibility already hides this tab for any repo whose
    # Repo.active_plugin_ids doesn't include "ukore_shot" (Settings > Repo >
    # Enable Plugin), the exact "appears only in the Sidebar of Enabled
    # repos" behavior asked for — no extra plumbing needed, see
    # launcher.py's section_key_to_plugin_id diffing.
    api.register_section(
        SectionSpec(
            key=PLUGIN_ID,
            label="UkoreShot",
            order=50,
            page_factory=lambda: UkoreShotPage(api=api),
        )
    )
    api.register_settings_tab(
        SettingsTabSpec(
            key=PLUGIN_ID,
            label="UkoreShot",
            order=125,
            page_factory=lambda: RepoVideoSettingsPage(api=api),
            on_activated=lambda page: page.refresh(),
            category=CATEGORY_REPO,
        )
    )
