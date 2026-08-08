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
