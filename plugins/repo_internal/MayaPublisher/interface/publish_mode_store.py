from __future__ import annotations

PLUGIN_ID = "maya_publisher"
_MODE_KEY = "publish_mode"

MODES = ("rig", "model", "animation")
MODE_LABELS = {"rig": "Rig", "model": "Model", "animation": "Animation"}


def _repo_key(project_id: str, repo_id: str) -> str:
    return f"{project_id}:{repo_id}"


def get_publish_mode(api, project_id: str, repo_id: str) -> str | None:
    """This repo's configured Publish Mode ("rig"/"model"/"animation"), or
    None if a studio admin hasn't set one yet. Resolves to
    data/plugins/core/maya_publisher.json — the same file
    PublishApi/tickets.py's ticket storage for tool_id "maya_publisher"
    also lands in (see interface/plugin_api.py's plugin_config_store,
    shared=True -> the "core" subdir)."""
    store = api.plugin_config_store(PLUGIN_ID, shared=True)
    return store.get(_MODE_KEY, {}).get(_repo_key(project_id, repo_id))


def set_publish_mode(api, project_id: str, repo_id: str, mode: str) -> None:
    store = api.plugin_config_store(PLUGIN_ID, shared=True)
    modes = store.get(_MODE_KEY, {})
    modes[_repo_key(project_id, repo_id)] = mode
    store.set(_MODE_KEY, modes)
