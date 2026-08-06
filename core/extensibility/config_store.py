from __future__ import annotations

import json
from pathlib import Path

from core.store import _atomic_write


class PluginConfigStore:
    """Namespaced, atomic-write JSON settings for a single plugin — mirrors
    LocalConfigStore/SystemConfigStore (core/store.py) but with a free-form
    key/value schema instead of fixed fields, since core/ can't know in
    advance what any given plugin wants to persist."""

    def __init__(self, json_path: Path):
        self.json_path = Path(json_path)
        self._data: dict = {}
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
