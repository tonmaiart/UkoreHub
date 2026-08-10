from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from core.extensibility.config_store import PluginConfigStore

_STATUS_KEY = "sync_status"


@dataclass
class SyncStatus:
    status: str
    message: str = ""
    updated_at: str = ""


class ExternalPluginSyncStatusStore:
    """Per-machine (non-shared) record of the last auto-sync result for each
    External Plugins catalog entry, keyed by CatalogEntry.id. Only
    conflict/error/broken_git results are ever written here (see
    sync_engine.PERSISTENT_STATUSES) — the sync engine runs headless (no
    Settings tab necessarily open), so this is what lets a stuck plugin's
    status survive until someone next opens Settings > Developer > External
    Plugins to notice it, instead of being lost the moment the sync
    finishes."""

    def __init__(self, config_store: PluginConfigStore):
        self._store = config_store

    def all_statuses(self) -> dict[str, SyncStatus]:
        raw = self._store.get(_STATUS_KEY, {})
        return {entry_id: SyncStatus(**data) for entry_id, data in raw.items()}

    def get(self, entry_id: str) -> SyncStatus | None:
        return self.all_statuses().get(entry_id)

    def set(self, entry_id: str, status: str, message: str = "") -> None:
        statuses = self._store.get(_STATUS_KEY, {})
        statuses[entry_id] = asdict(
            SyncStatus(status=status, message=message, updated_at=datetime.now(timezone.utc).isoformat())
        )
        self._store.set(_STATUS_KEY, statuses)

    def clear(self, entry_id: str) -> None:
        statuses = self._store.get(_STATUS_KEY, {})
        if entry_id in statuses:
            del statuses[entry_id]
            self._store.set(_STATUS_KEY, statuses)
