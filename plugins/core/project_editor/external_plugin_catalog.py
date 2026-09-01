from __future__ import annotations

import uuid
from dataclasses import dataclass

from plugin_api import ProjectPluginConfigStore, ValidationError

_CATALOG_KEY = "catalog"


@dataclass
class CatalogEntry:
    id: str
    name: str
    git_url: str
    folder_name: str
    # Cache of "what PluginManifest.id does this entry produce once cloned"
    # — unknown (None) until this session's sync engine (sync_engine.py) or
    # the Repository Settings manual clone-on-check flow has actually
    # cloned it and read its manifest.json once. Needed because
    # Repo.required_plugin_ids stores manifest ids, not this entry's own
    # uuid id, and a machine that has never cloned this entry has no other
    # way to map a required manifest id back to its git_url/folder_name.
    # See sync_engine.py's resolve_required_entries.
    plugin_id: str | None = None


def _is_safe_folder_name(folder_name: str) -> bool:
    return bool(folder_name) and folder_name not in (".", "..") and "/" not in folder_name and "\\" not in folder_name


class ExternalPluginCatalog:
    """The active Project's own catalog of cache/plugins/ repo plugins
    (cloned or not) — CRUD (Project Database tab, project_database_page.py),
    the auto-sync engine (sync_engine.py/sync_worker.py), and the "Plugins"
    Settings > Account status tab (external_plugin_updater_page.py) all
    share one instance of this class, built once in plugin.py's register().

    Used to be plugins/core/ExternalPluginManager/'s own catalog_store.py,
    with this file carrying a deliberate local duplicate (same
    don't-import-a-sibling-plugin's-source boundary
    required_repo_clone_worker.py still follows for its own case) — that
    plugin was merged into this one 2026-09-01 (its Settings > Project CRUD
    tab had already moved here earlier in the same 2026-09 merge), so
    there's no sibling left to duplicate against and this became the one
    canonical definition."""

    def __init__(self, config_store: ProjectPluginConfigStore | None):
        self._store = config_store

    def list_entries(self) -> list[CatalogEntry]:
        if self._store is None:
            return []
        raw = self._store.get(_CATALOG_KEY, [])
        return [CatalogEntry(**entry) for entry in raw]

    def _save(self, entries: list[CatalogEntry]) -> None:
        if self._store is None:
            return
        self._store.set(_CATALOG_KEY, [vars(entry) for entry in entries])

    def _validate(self, name: str, git_url: str, folder_name: str, *, existing_id: str | None = None) -> None:
        if not name.strip():
            raise ValidationError("Name is required.")
        if not git_url.strip():
            raise ValidationError("Git URL is required.")
        if not _is_safe_folder_name(folder_name):
            raise ValidationError("Folder Name must be a single folder name, not a path.")
        for entry in self.list_entries():
            if entry.id != existing_id and entry.folder_name == folder_name:
                raise ValidationError(f"Folder Name '{folder_name}' is already used by '{entry.name}'.")

    def add_entry(self, name: str, git_url: str, folder_name: str) -> CatalogEntry:
        self._validate(name, git_url, folder_name)
        entry = CatalogEntry(id=str(uuid.uuid4()), name=name.strip(), git_url=git_url.strip(), folder_name=folder_name)
        entries = self.list_entries()
        entries.append(entry)
        self._save(entries)
        return entry

    def edit_entry(self, entry_id: str, *, name: str, git_url: str, folder_name: str) -> None:
        self._validate(name, git_url, folder_name, existing_id=entry_id)
        entries = self.list_entries()
        for entry in entries:
            if entry.id == entry_id:
                entry.name = name.strip()
                entry.git_url = git_url.strip()
                entry.folder_name = folder_name
                break
        self._save(entries)

    def delete_entry(self, entry_id: str) -> None:
        entries = [entry for entry in self.list_entries() if entry.id != entry_id]
        self._save(entries)

    def update_plugin_id(self, entry_id: str, plugin_id: str) -> None:
        """Backfills CatalogEntry.plugin_id once it's learned from a real
        clone's manifest.json — see that field's own docstring. Silently a
        no-op for an entry_id that's since been deleted (a background sync
        result racing a manual Delete)."""
        entries = self.list_entries()
        for entry in entries:
            if entry.id == entry_id:
                entry.plugin_id = plugin_id
                break
        else:
            return
        self._save(entries)
