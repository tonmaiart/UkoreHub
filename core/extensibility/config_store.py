from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from core.storage.atomic_file import atomic_write
from core.storage.metadata_store import MetadataStore


class PluginConfigStore:
    """Namespaced, atomic-write JSON settings for a single plugin — mirrors
    LocalConfigStore/SystemConfigStore (core/storage/config_store.py) but
    with a free-form key/value schema instead of fixed fields, since core/
    can't know in advance what any given plugin wants to persist. `on_save`,
    when provided by the caller (interface/plugin_api.py, for shared=True
    stores only — see core/vcs/cloud_sync.py), pushes the freshly-saved file
    up to the shared studio bucket."""

    def __init__(self, json_path: Path, *, on_save: Callable[[], None] | None = None):
        self.json_path = Path(json_path)
        self._data: dict = {}
        self.on_save = on_save
        self.load()

    def load(self) -> None:
        if not self.json_path.exists():
            self._data = {}
            return
        self._data = json.loads(self.json_path.read_text(encoding="utf-8"))

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        atomic_write(self.json_path, self._data)
        if self.on_save:
            self.on_save()


class ProjectPluginConfigStore:
    """Same get/set interface as PluginConfigStore, but backed by the
    active Project's own plugin_data (core/models.py's Project) instead of
    a separate studio-wide JSON blob — for plugin data that's inherently
    session/project-scoped rather than studio-wide (e.g. maya_launcher's
    MAYA_ENV_BRIDGE contributions). Rides on MetadataStore's existing
    per-project cloud sync (pushed via _save_project) — no separate
    pull/push here, unlike PluginConfigStore(shared=True)."""

    def __init__(self, store: MetadataStore, project_id: str, plugin_id: str):
        self._store = store
        self._project_id = project_id
        self._plugin_id = plugin_id

    def get(self, key: str, default=None):
        return self._store.get_project_plugin_data(self._project_id, self._plugin_id).get(key, default)

    def set(self, key: str, value) -> None:
        data = self._store.get_project_plugin_data(self._project_id, self._plugin_id)
        data[key] = value
        self._store.set_project_plugin_data(self._project_id, self._plugin_id, data)
