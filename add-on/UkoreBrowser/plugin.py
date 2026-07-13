from __future__ import annotations

ADDON_ID = "ukore_browser"
# See add-on/MayaLauncher/plugin.py for the full contract this shared
# PluginConfigStore id and "contributions" shape follow.
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"


def register(api) -> None:
    addon_root = api.app_root / "add-on" / "UkoreBrowser"

    bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
    contributions = bridge.get("contributions", {})
    contributions[ADDON_ID] = {
        # api.app_root is contributed too so `import core.store` / `core.paths`
        # resolves inside Maya's Python — that's how core/repo_context.py talks
        # to UkoreHub's own Project/Repo model to find the active repo root.
        "PYTHONPATH": {ANY_VERSION: [str(addon_root / "maya-scripts"), str(api.app_root)]},
    }
    bridge.set("contributions", contributions)
