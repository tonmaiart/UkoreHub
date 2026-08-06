from __future__ import annotations

from pathlib import Path

from interface.section_registry import SectionSpec
from interface.settings_tab_registry import CATEGORY_REPO, SettingsTabSpec
from plugins.repo_internal.UkoreShot.interface.repo_video_settings_page import RepoVideoSettingsPage
from plugins.repo_internal.UkoreShot.interface.video_library_page import UkoreShotPage

PLUGIN_ID = "ukore_shot"
# This plugin's own images/ folder, not the shared data/icons/ every other
# plugin's SectionSpec.icon_path points at (see images/README.md's own
# note on this deliberate exception).
_ICON_PATH = Path(__file__).resolve().parent / "images" / "icons8-video-50.png"


def register(api) -> None:
    # A normal (non-persistent) section — main_window.py's
    # _apply_plugin_visibility already hides this tab for any repo whose
    # Repo.required_plugin_ids doesn't include "ukore_shot" (Settings >
    # Repo > Requirements & Plugins, opt-in since this plugin lives under
    # plugins/repo_internal/), the exact "appears only in the Sidebar of
    # opted-in repos" behavior asked for — no extra plumbing needed, see
    # launcher.py's section_key_to_plugin_id diffing.
    api.register_section(
        SectionSpec(
            key=PLUGIN_ID,
            label="UkoreShot",
            order=50,
            page_factory=lambda: UkoreShotPage(api=api),
            icon_path=_ICON_PATH,
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
