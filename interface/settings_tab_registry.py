from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from core.exceptions import ValidationError


@dataclass(frozen=True)
class SettingsTabSpec:
    key: str
    label: str
    order: int
    page_factory: Callable[[], QWidget]
    # Every settings page persists its own changes immediately (injecting
    # whatever store it needs at construction time, like ProgramDatabasePage
    # already does) — there's no dialog-level Save/Cancel anymore, so no
    # on_save/on_cancel here. on_activated is a different concern (display
    # refresh when this tab becomes visible, e.g. ProjectStatusPage).
    on_activated: Callable[[QWidget], None] | None = None


class SettingsTabRegistry:
    """Open, ordered replacement for the old hardcoded TAB_NAMES list +
    manual QStackedWidget wiring in settings_dialog.py."""

    def __init__(self) -> None:
        self._specs: dict[str, SettingsTabSpec] = {}

    def register(self, spec: SettingsTabSpec) -> None:
        if spec.key in self._specs:
            raise ValidationError(f"Settings tab key '{spec.key}' is already registered")
        self._specs[spec.key] = spec

    def ordered(self) -> list[SettingsTabSpec]:
        return sorted(self._specs.values(), key=lambda spec: (spec.order, spec.key))
