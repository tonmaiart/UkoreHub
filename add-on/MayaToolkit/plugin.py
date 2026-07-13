from __future__ import annotations

ADDON_ID = "maya_toolkit"
# See add-on/MayaLauncher/plugin.py for the full contract this shared
# PluginConfigStore id and "contributions" shape follow.
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"


def register(api) -> None:
    addon_root = api.app_root / "add-on" / "MayaToolkit"

    bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
    contributions = bridge.get("contributions", {})
    contributions[ADDON_ID] = {
        "PYTHONPATH": {ANY_VERSION: [str(addon_root / "maya-scripts")]},
        "MAYA_PLUG_IN_PATH": {ANY_VERSION: [str(addon_root / "maya-plug-ins")]},
    }
    bridge.set("contributions", contributions)
