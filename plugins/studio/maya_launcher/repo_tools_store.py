from __future__ import annotations

from core.extensibility.config_store import PluginConfigStore
from plugins.studio.maya_launcher.tools import TOOL_IDS

_KEY = "repo_enabled_tools"


class RepoToolsStore:
    """Per-repo enable/disable state for maya_launcher's 7 nested Maya
    tools — owned entirely by this plugin instead of the generic
    Repo.enabled_addon_ids mechanism (see plugins/studio/maya_launcher/README.md
    for why). Backed by a single shared PluginConfigStore
    (api.plugin_config_store("maya_launcher", shared=True)), keyed
    "<project_id>:<repo_id>" -> [tool_id, ...]."""

    def __init__(self, config_store: PluginConfigStore):
        self._config_store = config_store

    @staticmethod
    def _repo_key(project_id: str, repo_id: str) -> str:
        return f"{project_id}:{repo_id}"

    def enabled_tool_ids_for(self, project_id: str | None, repo_id: str | None) -> list[str]:
        """All 7 tool ids by default — matches the always-on behavior every
        repo has had until this store existed — unless this repo has an
        explicit entry (including an explicit empty list, which means "none
        enabled" and is honored as such)."""
        if not project_id or not repo_id:
            return list(TOOL_IDS)
        repo_map = self._config_store.get(_KEY, {})
        key = self._repo_key(project_id, repo_id)
        if key not in repo_map:
            return list(TOOL_IDS)
        return list(repo_map[key])

    def set_enabled_tool_ids(self, project_id: str, repo_id: str, tool_ids: list[str]) -> None:
        repo_map = self._config_store.get(_KEY, {})
        repo_map[self._repo_key(project_id, repo_id)] = list(tool_ids)
        self._config_store.set(_KEY, repo_map)
