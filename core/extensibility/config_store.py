from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from core.store import _atomic_write


class PluginConfigStore:
    """Namespaced, atomic-write JSON settings for a single plugin — mirrors
    LocalConfigStore/SystemConfigStore (core/store.py) but with a free-form
    key/value schema instead of fixed fields, since core/ can't know in
    advance what any given plugin wants to persist. `on_save`, when
    provided by the caller (interface/plugin_api.py, for shared=True
    stores only — see core/cloud_sync.py), pushes the freshly-saved file up
    to the shared studio bucket."""

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
        _atomic_write(self.json_path, self._data)
        if self.on_save:
            self.on_save()
