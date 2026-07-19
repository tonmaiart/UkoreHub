from __future__ import annotations

TOOL_ID = "maya_ngskin"
TOOL_LABEL = "MayaNgSkin"
# Convention-only string match with plugins/studio/maya_launcher/plugin.py
# — both resolve to the same data/plugins/studio/maya_launcher_env_bridge.json
# via PluginConfigStore, no coupling API needed. See that plugin's README
# for the full "contributions"/"labels" shape this writes into.
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"


def register(api) -> None:
    tool_root = api.app_root / "plugins" / "studio" / "MayaNgskin"

    # ngSkinTools2.mll is a compiled plug-in shipped once per Maya version
    # (maya-plug-ins/2018, .../2024, ...) — unlike a flat MAYA_PLUG_IN_PATH
    # entry, each version subfolder becomes its own keyed contribution.
    # Globs the folder rather than hardcoding a version list, so
    # adding/removing a version subfolder on disk needs no code change.
    plug_in_root = tool_root / "maya-plug-ins"
    versioned_plug_in_paths: dict[str, list[str]] = {}
    if plug_in_root.is_dir():
        for version_dir in sorted(plug_in_root.iterdir()):
            if version_dir.is_dir():
                versioned_plug_in_paths[version_dir.name] = [str(version_dir)]

    bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
    contributions = bridge.get("contributions", {})
    contributions[TOOL_ID] = {
        "PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts")]},
        "MAYA_PLUG_IN_PATH": versioned_plug_in_paths,
    }
    bridge.set("contributions", contributions)
    labels = bridge.get("labels", {})
    labels[TOOL_ID] = TOOL_LABEL
    bridge.set("labels", labels)
