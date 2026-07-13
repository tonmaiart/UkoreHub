from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from core.exceptions import ValidationError
from core.models import Repo


@dataclass(frozen=True)
class RepoAddonPanelSpec:
    addon_id: str
    panel_factory: Callable[[Repo], QWidget]


class RepoAddonPanelRegistry:
    """Plain id -> spec lookup (not an ordered list like the other
    registries) — the "Repo Add-on" tab only ever needs the panel for
    whichever add-ons a specific repo has enabled."""

    def __init__(self) -> None:
        self._specs: dict[str, RepoAddonPanelSpec] = {}

    def register(self, spec: RepoAddonPanelSpec) -> None:
        if spec.addon_id in self._specs:
            raise ValidationError(f"Repo add-on panel for '{spec.addon_id}' is already registered")
        self._specs[spec.addon_id] = spec

    def get(self, addon_id: str) -> RepoAddonPanelSpec | None:
        return self._specs.get(addon_id)
