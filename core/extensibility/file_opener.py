from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.models import Repo


@dataclass(frozen=True)
class FileOpenerSpec:
    addon_id: str
    extensions: frozenset[str]
    opener: Callable[[Path, Repo], bool]


class FileOpenerRegistry:
    """Lets a repo-scoped add-on claim responsibility for opening certain
    file extensions instead of falling back to the OS default association —
    e.g. launching Maya with custom environment variables instead of just
    `os.startfile()`. Gated by which add-ons the *active repo* has enabled
    (Repo.enabled_addon_ids), matching the existing Add-on model (per-repo
    opt-in, not a global always-on toggle like plugins/).

    Plain list, not a key->spec dict like the other registries — an add-on
    may register several extension groups, and there's no meaningful
    "duplicate" to reject here."""

    def __init__(self) -> None:
        self._specs: list[FileOpenerSpec] = []

    def register(self, spec: FileOpenerSpec) -> None:
        self._specs.append(spec)

    def find_opener(self, path: Path, enabled_addon_ids: list[str]) -> Callable[[Path, Repo], bool] | None:
        suffix = path.suffix.lower()
        enabled = set(enabled_addon_ids)
        for spec in self._specs:
            if spec.addon_id in enabled and suffix in spec.extensions:
                return spec.opener
        return None
