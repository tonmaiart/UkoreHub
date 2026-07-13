from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from core.exceptions import ValidationError


@dataclass(frozen=True)
class ProjectInfoTabSpec:
    key: str
    label: str
    order: int
    page_factory: Callable[[], QWidget]


class ProjectInfoTabRegistry:
    """Open, ordered registry of sub-tabs shown inside the Project
    Information section — the built-in "Main" tab registers into this the
    same way a plugin's `register_project_info_tab(...)` would."""

    def __init__(self) -> None:
        self._specs: dict[str, ProjectInfoTabSpec] = {}

    def register(self, spec: ProjectInfoTabSpec) -> None:
        if spec.key in self._specs:
            raise ValidationError(f"Project info tab key '{spec.key}' is already registered")
        self._specs[spec.key] = spec

    def ordered(self) -> list[ProjectInfoTabSpec]:
        return sorted(self._specs.values(), key=lambda spec: (spec.order, spec.key))
