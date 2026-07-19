from __future__ import annotations

TOOL_ID = "mgear"
TOOL_LABEL = "mGear"
# Convention-only string match with plugins/studio/maya_launcher/plugin.py
# — both resolve to the same data/plugins/studio/maya_launcher_env_bridge.json
# via PluginConfigStore, no coupling API needed. See that plugin's README
# for the full "contributions"/"labels" shape this writes into.
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"


def register(api) -> None:
    tool_root = api.app_root / "plugins" / "studio" / "mGear"

    bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
    contributions = bridge.get("contributions", {})
    contributions[TOOL_ID] = {
        # maya-modules/mGear.mod is itself version-aware (+MAYAVERSION:2018
        # ... / +MAYAVERSION:2019 ... blocks) — Maya resolves the right
        # platform/version subfolder from the .mod file once
        # MAYA_MODULE_PATH points at its flat parent folder, so no
        # per-version keying is needed here (contrast with MayaNgskin's
        # compiled, one-build-per-version .mll).
        "MAYA_MODULE_PATH": {ANY_VERSION: [str(tool_root / "maya-modules")]},
        "MGEAR_SHIFTER_COMPONENT_PATH": {ANY_VERSION: [str(tool_root / "mgear-custom-component")]},
    }
    bridge.set("contributions", contributions)
    labels = bridge.get("labels", {})
    labels[TOOL_ID] = TOOL_LABEL
    bridge.set("labels", labels)
