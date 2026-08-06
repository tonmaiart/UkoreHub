from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.models import Repo


@dataclass(frozen=True)
class FileOpenerSpec:
    plugin_id: str
    extensions: frozenset[str]
    opener: Callable[[Path, Repo], bool]


class FileOpenerRegistry:
    """Lets a plugin claim responsibility for opening certain file
    extensions instead of falling back to the OS default association —
    e.g. launching Maya with custom environment variables instead of just
    `os.startfile()`.

    Plain list, not a key->spec dict like the other registries — a plugin
    may register several extension groups, and there's no meaningful
    "duplicate" to reject here."""

    def __init__(self) -> None:
        self._specs: list[FileOpenerSpec] = []

    def register(self, spec: FileOpenerSpec) -> None:
        self._specs.append(spec)

    def find_opener(self, path: Path) -> Callable[[Path, Repo], bool] | None:
        suffix = path.suffix.lower()
        for spec in self._specs:
            if suffix in spec.extensions:
                return spec.opener
        return None
