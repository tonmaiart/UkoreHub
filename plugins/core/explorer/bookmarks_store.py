from __future__ import annotations

from pathlib import Path

from plugin_api import MetadataStore

_PLUGIN_ID = "explorer"
_DATA_KEY = "bookmarks"


class BookmarksStore:
    """Per-repo bookmark list, stored on Repo.plugin_data via
    MetadataStore.get_repo_plugin_data/set_repo_plugin_data — that data
    lives inside the repo's own project blob (data/projects/<id>.json),
    which is already cloud-synced, so bookmarks show up on every machine
    without a separate synced file (see plugins-guide.md's "Sharing data
    with another plugin" section)."""

    def __init__(self, metadata_store: MetadataStore, project_id: str, repo_id: str, repo_root: Path):
        self._metadata_store = metadata_store
        self._project_id = project_id
        self._repo_id = repo_id
        self.repo_root = Path(repo_root)

    def _load(self) -> list[str]:
        entry = self._metadata_store.get_repo_plugin_data(self._project_id, self._repo_id, _PLUGIN_ID)
        return list(entry.get(_DATA_KEY, []))

    def _save(self, relpaths: list[str]) -> None:
        entry = dict(self._metadata_store.get_repo_plugin_data(self._project_id, self._repo_id, _PLUGIN_ID))
        entry[_DATA_KEY] = relpaths
        self._metadata_store.set_repo_plugin_data(self._project_id, self._repo_id, _PLUGIN_ID, entry)

    def add(self, abs_path: Path) -> list[Path]:
        try:
            rel = str(Path(abs_path).resolve().relative_to(self.repo_root.resolve()))
        except ValueError:
            return self.get_bookmarks()

        relpaths = self._load()
        if rel not in relpaths:
            relpaths.append(rel)
            self._save(relpaths)
        return self.get_bookmarks()

    def remove(self, abs_path: Path) -> list[Path]:
        try:
            rel = str(Path(abs_path).resolve().relative_to(self.repo_root.resolve()))
        except ValueError:
            return self.get_bookmarks()

        relpaths = self._load()
        if rel in relpaths:
            relpaths.remove(rel)
            self._save(relpaths)
        return self.get_bookmarks()

    def get_bookmarks(self) -> list[Path]:
        # Filters missing-on-disk entries for display only — does not persist the
        # removal. This store is cloud-synced/shared across the whole team, and a
        # missing file here often just means this machine hasn't pulled/cloned it
        # yet, not that the bookmark is actually gone; auto-saving the pruned list
        # would delete it for every other artist too. Real removal only happens via
        # remove() (the explicit "Remove Bookmark" action).
        relpaths = self._load()
        paths = []
        for rel in relpaths:
            abs_path = self.repo_root / rel
            if abs_path.exists():
                paths.append(abs_path)
        return paths
