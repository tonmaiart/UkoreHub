from __future__ import annotations

ADDON_ID = "maya_ngskin"
# See add-on/MayaLauncher/plugin.py for the full contract this shared
# PluginConfigStore id and "contributions" shape follow.
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"


def register(api) -> None:
    addon_root = api.app_root / "add-on" / "MayaNgskin"

    # ngSkinTools2.mll is a compiled plug-in shipped once per Maya version
    # (maya-plug-ins/2018, .../2024, ...) — unlike the other Maya add-ons
    # here, a single flat MAYA_PLUG_IN_PATH entry can't cover every version,
    # so each version subfolder becomes its own keyed contribution. Globs
    # the folder rather than hardcoding a version list, so adding/removing
    # a version subfolder on disk needs no code change.
    plug_in_root = addon_root / "maya-plug-ins"
    versioned_plug_in_paths = {}
    if plug_in_root.is_dir():
        for version_dir in sorted(plug_in_root.iterdir()):
            if version_dir.is_dir():
                versioned_plug_in_paths[version_dir.name] = [str(version_dir)]

    bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
    contributions = bridge.get("contributions", {})
    contributions[ADDON_ID] = {
        "PYTHONPATH": {ANY_VERSION: [str(addon_root / "maya-scripts")]},
        "MAYA_PLUG_IN_PATH": versioned_plug_in_paths,
    }
    bridge.set("contributions", contributions)
