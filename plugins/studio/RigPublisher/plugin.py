from __future__ import annotations

from interface.settings_tab_registry import CATEGORY_REPO, SettingsTabSpec
from plugins.studio.RigPublisher.settings_page import RigPublisherSettingsPage

TOOL_ID = "rig_publisher"
TOOL_LABEL = "RigPublisher"
# Convention-only string match with plugins/studio/maya_launcher/plugin.py
# — both resolve to the same data/plugins/studio/maya_launcher_env_bridge.json
# via PluginConfigStore, no coupling API needed. See that plugin's README
# for the full "contributions"/"labels" shape this writes into. Relies on
# plugins/studio/MayaToolkit (UkoreMaya.core.Pipeline) and
# plugins/studio/PublishApi also being enabled — not imported directly,
# just expected to be on the same merged PYTHONPATH at Maya launch time.
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"


def register(api) -> None:
    tool_root = api.app_root / "plugins" / "studio" / "RigPublisher"

    bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
    contributions = bridge.get("contributions", {})
    contributions[TOOL_ID] = {
        "PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts")]},
    }
    bridge.set("contributions", contributions)
    labels = bridge.get("labels", {})
    labels[TOOL_ID] = TOOL_LABEL
    bridge.set("labels", labels)

    api.register_settings_tab(
        SettingsTabSpec(
            key=TOOL_ID,
            label=TOOL_LABEL,
            order=122,
            page_factory=lambda: RigPublisherSettingsPage(api=api),
            on_activated=lambda page: page.refresh(),
            category=CATEGORY_REPO,
        )
    )
