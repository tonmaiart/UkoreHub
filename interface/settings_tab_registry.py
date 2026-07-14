from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from core.exceptions import ValidationError

# Which "am I editing the whole app, just repo/project data, or internal/
# admin plumbing" bucket a tab falls into — SettingsView renders one
# section per category, in this order, with a header row between them. A
# plugin's own settings tab defaults to CATEGORY_GENERAL (most plugin
# settings are machine/software-wide, e.g. Software Linker) — opt into
# CATEGORY_REPO explicitly when the tab's content is actually about the
# active repo (e.g. Maya Launcher's per-repo tool toggles), or
# CATEGORY_DEVELOPER for studio-admin/internal-plumbing tabs (GitHub OAuth
# Client ID, Program Database, Plugins, Project Data Editor) that most
# users never need to open. CATEGORY_REPO's header row is relabeled to the
# active repo's own name at runtime — see SettingsView.set_active_repo_name
# — so CATEGORY_LABELS[CATEGORY_REPO] is only the fallback shown when no
# repo is active.
CATEGORY_GENERAL = "general"
CATEGORY_REPO = "repo"
CATEGORY_DEVELOPER = "developer"
CATEGORY_LABELS = {CATEGORY_GENERAL: "General", CATEGORY_REPO: "Repo", CATEGORY_DEVELOPER: "Developer"}


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
    category: str = CATEGORY_GENERAL


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
