from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.exceptions import GitOperationError
from core.extensibility.loader import DiscoveredPlugin, plugin_source
from core.models import Repo
from core.vcs.git_service import GitService
from plugins.core.ExternalPlugins.catalog_store import CatalogEntry, ExternalPluginCatalog

STATUS_CLONED = "cloned"
STATUS_UP_TO_DATE = "up_to_date"
STATUS_CONFLICT = "conflict"
STATUS_BROKEN_GIT = "broken_git"
STATUS_ERROR = "error"

# Statuses worth remembering in ExternalPluginSyncStatusStore past the run
# that produced them — the rest (cloned/up_to_date) are fine to just
# disappear once resolved, see sync_status_store.py.
PERSISTENT_STATUSES = {STATUS_CONFLICT, STATUS_ERROR, STATUS_BROKEN_GIT}


@dataclass
class SyncResult:
    entry_id: str
    status: str
    message: str = ""


@dataclass
class PluginIdBackfill:
    entry_id: str
    plugin_id: str


def resolve_required_entries(
    repo: Repo,
    catalog: ExternalPluginCatalog,
    plugin_catalog: list[DiscoveredPlugin],
) -> tuple[list[CatalogEntry], list[PluginIdBackfill]]:
    """Which catalog entries repo.required_plugin_ids resolves to, plus any
    CatalogEntry.plugin_id gaps this session's already-discovered
    plugin_catalog can backfill for free (matched by folder_name — reuses
    core/extensibility/loader.py's one-shot startup discover_plugins()
    result already passed in, no extra manifest.json parsing here).

    A required manifest id with no catalog entry's plugin_id resolving to it
    (neither already cached nor backfillable from this session's discovered
    plugins) is simply skipped — nothing to clone/pull it from yet. See this
    plugin's own README for why that's an accepted gap, not a bug."""
    entries = catalog.list_entries()
    discovered_by_folder = {
        plugin.dir_path.name: plugin for plugin in plugin_catalog if plugin_source(plugin) == "repo"
    }

    backfills: list[PluginIdBackfill] = []
    resolved_plugin_id_by_entry: dict[str, str] = {}
    for entry in entries:
        if entry.plugin_id:
            resolved_plugin_id_by_entry[entry.id] = entry.plugin_id
            continue
        discovered = discovered_by_folder.get(entry.folder_name)
        if discovered is not None:
            resolved_plugin_id_by_entry[entry.id] = discovered.manifest.id
            backfills.append(PluginIdBackfill(entry_id=entry.id, plugin_id=discovered.manifest.id))

    required_ids = set(repo.required_plugin_ids)
    resolved = [entry for entry in entries if resolved_plugin_id_by_entry.get(entry.id) in required_ids]
    return resolved, backfills


def sync_entry(git_service: GitService, plugins_root: Path, entry: CatalogEntry) -> SyncResult:
    """Clone-if-missing / pull-if-present for one catalog entry. Never
    forces, aborts, or discards anything — a merge conflict is left exactly
    as git leaves it, for a dev to resolve by hand (e.g. via the settings
    tab's existing "Open Git Directory" action) rather than being silently
    papered over. A clone/folder already mid-merge from an earlier failed
    sync is detected before attempting another pull() (which would just
    fail again the same way), so it keeps reporting the same conflict
    instead of retrying every launch."""
    local_path = plugins_root / entry.folder_name

    if not git_service.is_cloned(local_path):
        if not entry.git_url:
            return SyncResult(entry.id, STATUS_ERROR, "No Git URL set for this catalog entry.")
        try:
            git_service.clone(entry.git_url, local_path)
        except GitOperationError as exc:
            return SyncResult(entry.id, STATUS_ERROR, str(exc))
        return SyncResult(entry.id, STATUS_CLONED)

    # is_repo_root(), not just is_cloned() — see this plugin's README's "Why
    # is_repo_root, not just is_cloned" (bug-history 2026-08-08): a broken
    # empty .git left by an interrupted clone must never have a real git
    # command run against it, since git's own discovery would silently walk
    # up to whatever real repo is further up the tree instead.
    if not git_service.is_repo_root(local_path):
        return SyncResult(entry.id, STATUS_BROKEN_GIT, "Broken .git directory — delete the folder and Clone again.")

    if git_service.has_unresolved_merge(local_path):
        return SyncResult(
            entry.id,
            STATUS_CONFLICT,
            "Merge conflict from a previous update — resolve it in the clone (Open Git Directory), "
            "then commit or abort the merge.",
        )

    try:
        git_service.pull(local_path)
    except GitOperationError as exc:
        if git_service.has_unresolved_merge(local_path):
            return SyncResult(entry.id, STATUS_CONFLICT, str(exc))
        return SyncResult(entry.id, STATUS_ERROR, str(exc))
    return SyncResult(entry.id, STATUS_UP_TO_DATE)
