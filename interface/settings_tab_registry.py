from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from interface.registry_base import KeyedOrderedRegistry

# Which "am I editing the whole app, just repo/project data, or internal/
# admin plumbing" bucket a tab falls into — SettingsView renders one
# section per category, in this order, with a header row between them. A
# plugin's own settings tab defaults to CATEGORY_GENERAL (most plugin
# settings are machine/software-wide, e.g. Software Linker) — opt into
# CATEGORY_REPO explicitly when the tab's content is actually about the
# active repo (e.g. Maya Launcher's per-repo tool toggles), or
# CATEGORY_DEVELOPER for studio-admin/internal-plumbing tabs (GitHub OAuth
# Client ID, Program Database, Plugins) that most users never need to
# open. CATEGORY_REPO tabs are registered here like any other but are not
# rendered by SettingsView (see that class's docstring) — they render
# generically as collapsible sections in plugins/studio/project_editor/'s
# right panel instead. CATEGORY_LABELS[CATEGORY_REPO] is only used there.
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
    # refresh when this tab becomes visible, e.g. LocalRepositoryPage).
    on_activated: Callable[[QWidget], None] | None = None
    category: str = CATEGORY_GENERAL


class SettingsTabRegistry(KeyedOrderedRegistry[SettingsTabSpec]):
    """Open, ordered replacement for the old hardcoded TAB_NAMES list +
    manual QStackedWidget wiring in settings_dialog.py. register()/
    ordered()/keys() come from KeyedOrderedRegistry
    (interface/registry_base.py)."""

    def __init__(self) -> None:
        super().__init__(label="Settings tab")
