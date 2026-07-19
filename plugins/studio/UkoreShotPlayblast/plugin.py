from __future__ import annotations

TOOL_ID = "ukore_shot_playblast"
TOOL_LABEL = "UkoreShotPlayblast"
# Convention-only string match with plugins/studio/maya_launcher/plugin.py
# — both resolve to the same data/plugins/studio/maya_launcher_env_bridge.json
# via PluginConfigStore, no coupling API needed. See that plugin's README
# for the full "contributions"/"labels" shape this writes into — same
# pattern plugins/studio/RigPublisher/plugin.py uses for its own Maya
# package.
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"


def register(api) -> None:
    # Pure infrastructure — no artist-facing behavior or UI of its own on
    # the UkoreHub desktop side (confirmed with the user 2026-07-19: this
    # tool's options belong entirely inside Maya, not a Repository Setting
    # tab — see maya-scripts/UkoreShotPlayblast/options_dialog.py's
    # "Playblast Options..." menu item instead, same "pure infra, no UI of
    # its own" reasoning plugins/studio/maya_launcher/plugin.py's own
    # PUBLISH_API_TOOL_ID comment gives for plugins/studio/PublishApi).
    # This register() call only ever contributes the PYTHONPATH bridge
    # entry so Maya can import this plugin's own
    # maya-scripts/UkoreShotPlayblast package — core.* importability
    # itself already comes from PublishApi's own contribution (it also
    # adds api.app_root to PYTHONPATH), not from this plugin's.
    tool_root = api.app_root / "plugins" / "studio" / "UkoreShotPlayblast"

    bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
    contributions = bridge.get("contributions", {})
    contributions[TOOL_ID] = {"PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts")]}}
    bridge.set("contributions", contributions)
    labels = bridge.get("labels", {})
    labels[TOOL_ID] = TOOL_LABEL
    bridge.set("labels", labels)
