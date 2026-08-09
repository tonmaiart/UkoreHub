from __future__ import annotations

from pathlib import Path

TOOL_ID = "ukore_playblast"
TOOL_LABEL = "UkorePlayblast"
# Convention-only string match with plugins/repo_internal/maya_launcher/plugin.py
# — both resolve to the same active Project's plugin_data via
# ProjectPluginConfigStore, no coupling API needed. See that plugin's README
# for the full "contributions"/"labels" shape this writes into — same
# pattern plugins/repo_internal/MayaPublisher/plugin.py uses for its own Maya
# package.
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"


def register(api) -> None:
    # Pure infrastructure — no artist-facing behavior or UI of its own on
    # the UkoreHub desktop side (confirmed with the user 2026-07-19: this
    # tool's options belong entirely inside Maya, not a Repository Setting
    # tab — see maya-scripts/UkorePlayblast/options_dialog.py's
    # "Playblast Options..." menu item instead, same "pure infra, no UI of
    # its own" reasoning plugins/repo_internal/maya_launcher/plugin.py's own
    # PUBLISH_API_TOOL_ID comment gives for plugins/repo_internal/PublishApi).
    # This register() call only ever contributes the PYTHONPATH bridge
    # entry so Maya can import this plugin's own
    # maya-scripts/UkorePlayblast package — core.* importability
    # itself already comes from PublishApi's own contribution (it also
    # adds api.app_root to PYTHONPATH), not from this plugin's.
    tool_root = Path(__file__).resolve().parent

    bridge = api.project_plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID)
    if bridge is None:
        return
    contributions = bridge.get("contributions", {})
    contributions[TOOL_ID] = {"PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts")]}}
    bridge.set("contributions", contributions)
    labels = bridge.get("labels", {})
    labels[TOOL_ID] = TOOL_LABEL
    bridge.set("labels", labels)
