from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from plugin_api import DiscoveredPlugin, GitService, Repo
from plugins.core.ExternalPluginManager.catalog_store import ExternalPluginCatalog
from plugins.core.ExternalPluginManager.sync_engine import resolve_required_entries, sync_entry


class ExternalPluginSyncWorker(QThread):
    """Clones/pulls every External Plugins catalog entry the given repo
    requires, sequentially — never in parallel, since two git commands
    racing on the same cache/plugins/<folder> clone could corrupt it. Runs
    entirely off the main thread (see this plugin's README's "Auto-sync
    runs on a background thread"); every git call here is a plain
    subprocess call with no Qt/UI object touched from this thread.

    Never writes to the catalog or the status store directly from run() —
    only ever emits signals, which Qt queues onto the thread the receiving
    slot actually lives on (the main thread, here). That's what makes it
    safe for the controller (plugin.py's _SyncController) to apply catalog
    plugin_id backfills and status-store writes without any locking."""

    entry_synced = Signal(str, str, str)  # entry_id, status, message
    backfill_ready = Signal(str, str)  # entry_id, plugin_id

    def __init__(
        self,
        *,
        git_service: GitService,
        plugins_root: Path,
        repo: Repo,
        catalog: ExternalPluginCatalog,
        plugin_catalog: list[DiscoveredPlugin],
        parent=None,
    ):
        super().__init__(parent)
        self._git_service = git_service
        self._plugins_root = plugins_root
        self._repo = repo
        self._catalog = catalog
        self._plugin_catalog = plugin_catalog

    def run(self) -> None:
        entries, backfills = resolve_required_entries(self._repo, self._catalog, self._plugin_catalog)
        for backfill in backfills:
            self.backfill_ready.emit(backfill.entry_id, backfill.plugin_id)
        for entry in entries:
            result = sync_entry(self._git_service, self._plugins_root, entry)
            self.entry_synced.emit(result.entry_id, result.status, result.message)
