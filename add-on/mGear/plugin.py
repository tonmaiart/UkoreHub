from __future__ import annotations

ADDON_ID = "mgear"
# See add-on/MayaLauncher/plugin.py for the full contract this shared
# PluginConfigStore id and "contributions" shape follow.
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"


def register(api) -> None:
    addon_root = api.app_root / "add-on" / "mGear"

    # maya-modules/mGear.mod is a real Maya .mod file, itself version-aware
    # (+ MAYAVERSION:2018 ... / +MAYAVERSION:2019 ... per block) — Maya
    # resolves the right platform/version subfolder from the .mod file
    # once MAYA_MODULE_PATH points at its flat parent folder, so no
    # per-version keying is needed here (contrast with MayaNgskin).
    bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
    contributions = bridge.get("contributions", {})
    contributions[ADDON_ID] = {
        "MAYA_MODULE_PATH": {ANY_VERSION: [str(addon_root / "maya-modules")]},
        "MGEAR_SHIFTER_COMPONENT_PATH": {ANY_VERSION: [str(addon_root / "mgear-custom-component")]},
    }
    bridge.set("contributions", contributions)
