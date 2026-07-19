"""Per-repo, per-user local cache of files opened via a table double-click
in Explorer's RepoBrowserWidget.

Mirrors plugins/studio/UkoreBrowser/maya-scripts/UkoreBrowser/core/browser_config.py's
BrowserConfig — same <repo_root>/.ukorehub/ convention, same repo-relative
path storage (survives a different drive letter machine to machine) — but
scoped per OS user too (the filename includes it), since this is a
genuinely per-artist working list, not something meant to be shared even
between two people using the same clone. Never committed by the studio's
own repo — the same as UkoreBrowser's own recent-files file, this lives
inside a production repo's working tree, not this app's, so keeping it out
of that repo's git history is that repo's own .gitignore's job, not
something this file can enforce."""

from __future__ import annotations

import getpass
import json
import re
from pathlib import Path

_CONFIG_DIRNAME = ".ukorehub"
_FILENAME_TEMPLATE = "explorer_last_opened_{username}.json"
# Keeps the filename filesystem-safe regardless of what the OS username
# actually contains (spaces, unicode, etc.) — matches only the characters
# every OS allows unescaped in a filename.
_SAFE_USERNAME_PATTERN = re.compile(r"[^A-Za-z0-9_-]+")


def _safe_username() -> str:
    try:
        username = getpass.getuser()
    except Exception:
        return "unknown"
    return _SAFE_USERNAME_PATTERN.sub("_", username) or "unknown"


class LastOpenedStore:
    def __init__(self, repo_root: Path, max_entries: int = 20):
        self.repo_root = Path(repo_root)
        self.max_entries = max_entries
        self._config_path = self.repo_root / _CONFIG_DIRNAME / _FILENAME_TEMPLATE.format(username=_safe_username())
        self._relpaths: list[str] = self._load()

    def _load(self) -> list[str]:
        if not self._config_path.is_file():
            return []
        try:
            data = json.loads(self._config_path.read_text(encoding="utf-8"))
            return list(data.get("last_opened", []))
        except Exception:
            return []

    def _save(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps({"last_opened": self._relpaths}, indent=4), encoding="utf-8"
        )

    def get_last_opened(self) -> list[Path]:
        """Absolute paths, most-recently-opened first. Entries whose file
        no longer exists are dropped (and the drop persisted), since a
        stale entry is never useful and would just clutter the list."""
        still_valid = []
        paths = []
        for rel in self._relpaths:
            abs_path = self.repo_root / rel
            if abs_path.exists():
                still_valid.append(rel)
                paths.append(abs_path)
        if still_valid != self._relpaths:
            self._relpaths = still_valid
            self._save()
        return paths

    def add(self, abs_path: Path) -> list[Path]:
        try:
            rel = str(Path(abs_path).relative_to(self.repo_root))
        except ValueError:
            return self.get_last_opened()  # outside this repo root — not our concern
        if rel in self._relpaths:
            self._relpaths.remove(rel)
        self._relpaths.insert(0, rel)
        self._relpaths = self._relpaths[: self.max_entries]
        self._save()
        return self.get_last_opened()
