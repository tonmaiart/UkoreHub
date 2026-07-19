from __future__ import annotations

TOOL_ID = "publish_api"
TOOL_LABEL = "PublishApi"
# Convention-only string match with plugins/studio/maya_launcher/plugin.py
# — both resolve to the same data/plugins/studio/maya_launcher_env_bridge.json
# via PluginConfigStore, no coupling API needed. See that plugin's README
# for the full "contributions"/"labels" shape this writes into.
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"


def register(api) -> None:
    tool_root = api.app_root / "plugins" / "studio" / "PublishApi"

    bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
    contributions = bridge.get("contributions", {})
    contributions[TOOL_ID] = {
        # api.app_root is contributed too so `import core.store` / `core.paths`
        # / `core.extensibility.config_store` resolve inside Maya's Python —
        # that's how repo_paths.py talks to UkoreHub's own Project/Repo/
        # pipeline model. Same convention plugins/studio/UkoreBrowser/
        # plugin.py already uses for the same reason.
        "PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts"), str(api.app_root)]},
    }
    bridge.set("contributions", contributions)
    labels = bridge.get("labels", {})
    labels[TOOL_ID] = TOOL_LABEL
    bridge.set("labels", labels)
