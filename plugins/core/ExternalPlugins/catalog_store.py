from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.exceptions import ValidationError
from core.extensibility.config_store import PluginConfigStore

_CATALOG_KEY = "catalog"


@dataclass
class CatalogEntry:
    id: str
    name: str
    git_url: str
    folder_name: str
    # Cache of "what PluginManifest.id does this entry produce once cloned"
    # — unknown (None) until some machine's sync engine (or the Requirements
    # & Plugins manual clone-on-check flow) has actually cloned it and read
    # its manifest.json once. Needed because Repo.required_plugin_ids stores
    # manifest ids, not this entry's own uuid id, and a machine that has
    # never cloned this entry has no other way to map a required manifest id
    # back to this entry's git_url/folder_name. See
    # plugins/core/ExternalPlugins/sync_engine.py's resolve_required_entries
    # and this plugin's own README.
    plugin_id: str | None = None


def _is_safe_folder_name(folder_name: str) -> bool:
    """A single path segment — no separators or traversal, since this is
    used directly as `cache/plugins/<folder_name>`."""
    return bool(folder_name) and folder_name not in (".", "..") and "/" not in folder_name and "\\" not in folder_name


class ExternalPluginCatalog:
    """Studio-wide list of known cache/plugins/ repo plugins (cloned or
    not), backed by a shared PluginConfigStore — same "namespaced JSON,
    git-tracked" convention every other cross-machine plugin setting
    uses (see plugins/README.md's "Sharing data with another plugin")."""

    def __init__(self, config_store: PluginConfigStore):
        self._store = config_store

    def list_entries(self) -> list[CatalogEntry]:
        # Always re-read the backing file first — this store is built once
        # at app startup and then held for the whole session (plugin.py's
        # _SyncController), so its in-memory copy can silently go stale
        # whenever something else changes the file without going through
        # this exact object: another machine pushing a newer catalog, or a
        # push conflict on this machine (core/vcs/cloud_sync.py's
        # GcsJsonSync.push() reloads the *file* on a 412 but has no way to
        # reach back into this in-memory PluginConfigStore to refresh it
        # too). Without this, a stuck-stale catalog here would keep
        # disagreeing with anything that reads the file fresh (e.g.
        # interface/repo_settings/requirements_and_plugins_page.py's
        # _read_external_catalog()) for the rest of the session.
        self._store.load()
        raw = self._store.get(_CATALOG_KEY, [])
        return [CatalogEntry(**entry) for entry in raw]

    def _save(self, entries: list[CatalogEntry]) -> None:
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
