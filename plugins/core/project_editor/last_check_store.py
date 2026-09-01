from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from plugin_api import PluginConfigStore

_RESULT_KEY = "last_check_result"


@dataclass
class LastCheckResult:
    status: str
    detail: str = ""
    checked_at: str = ""


class LastCheckedStore:
    """Per-machine (non-shared) record of the last "Check for Status" result
    (status bucket + detail + when) for each External Plugins catalog entry,
    keyed by CatalogEntry.id. Kept in its own top-level JSON key, separate
    from ExternalPluginSyncStatusStore's `sync_status` (sync_status_store.py)
    — that record is set/cleared wholesale by the auto-sync engine
    (plugin.py's _SyncController._on_entry_synced) on every app start/repo
    switch, which would otherwise wipe out a manual check's cached result.

    external_plugin_updater_page.py's fast, local-only _local_status() reads
    this back on every refresh (e.g. reopening the tab) so a network-derived
    result like "3 commits behind" survives instead of reverting to a bare
    "Up to date" until the next explicit Check for Status."""

    def __init__(self, config_store: PluginConfigStore):
        self._store = config_store

    def get(self, entry_id: str) -> LastCheckResult | None:
        raw = self._store.get(_RESULT_KEY, {})
        data = raw.get(entry_id)
        return LastCheckResult(**data) if data is not None else None

    def set(self, entry_id: str, status: str, detail: str = "") -> None:
        results = self._store.get(_RESULT_KEY, {})
        results[entry_id] = asdict(
            LastCheckResult(status=status, detail=detail, checked_at=datetime.now(timezone.utc).isoformat())
        )
        self._store.set(_RESULT_KEY, results)

    def clear(self, entry_id: str) -> None:
        results = self._store.get(_RESULT_KEY, {})
        if entry_id in results:
            del results[entry_id]
            self._store.set(_RESULT_KEY, results)
