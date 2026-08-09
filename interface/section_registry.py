from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QWidget

from interface.registry_base import KeyedOrderedRegistry


@dataclass(frozen=True)
class UICommandService:
    """Passed to SectionSpec.wire(page, host) — named SectionHost before
    this refactor; renamed to reflect what it actually is: a single command
    surface a plugin page calls into, not a per-section "host" object. A
    fixed, small set of named callbacks — not a generic event bus —
    mirroring background_threads' shape below: MainWindow invokes wire()
    generically, the closure reaches into the page's own internals. Add a
    new named field only on demonstrated need, not speculatively."""

    set_status_message: Callable[[str], None]
    navigate_and_focus: Callable[[str, Path], None]
    # Lets a section's page trigger a real active-repo switch (e.g. on
    # node click in plugins/core/project_editor's graph view) without
    # holding a MainWindow reference — wraps MainWindow._set_active_repo.
    set_active_repo: Callable[[str, str], None]
    # Lets a section jump straight to one SettingsTabSpec's tab inside the
    # Setting popup (e.g. plugins/core/program_launcher/'s "Open Setting"
    # button for an unlinked Program, landing on Software Linker) without
    # holding a MainWindow reference. Wraps
    # MainWindow._on_settings_requested(select_key=...) ->
    # SettingsDialog.select_tab. A key with no matching tab is a no-op —
    # the dialog still opens, just on its normal default tab.
    open_settings_tab: Callable[[str], None]
    # Lets a section's page trigger the app's "different project" flow
    # without holding a MainWindow reference — wraps
    # MainWindow._request_switch_project. Project is fixed for the whole
    # run (LocalConfigStore.active_project_id, set once by launcher.py's
    # mandatory Project Selector gate), so this is a real restart back
    # through that gate, not an in-place state change. Added specifically
    # for plugins/core/project_editor's Settings > Project "Switch
    # Project..." button.
    switch_project: Callable[[], None]


@dataclass(frozen=True)
class SectionSpec:
    key: str
    label: str
    order: int
    page_factory: Callable[[], QWidget]
    # Optional: given the constructed page, return any background QThread
    # workers it owns, so MainWindow.closeEvent can terminate them safely
    # without needing to know a plugin page's internals.
    background_threads: Callable[[QWidget], list] | None = None
    # Optional: icon shown next to the label in Sidebar's SectionTabList row
    # for this section. A section without one falls back to text-only (e.g.
    # a plugin that hasn't supplied an icon yet).
    icon_path: Path | None = None
    # Optional: a small widget shown at the right edge of this section's own
    # row in Sidebar's SectionTabList (e.g. plugins/core/Notification/'s
    # unread-count badge) — built once, alongside page_factory, and never
    # rebuilt by SectionTabList. The plugin that supplies the factory keeps
    # its own reference to the returned widget and updates it directly
    # (text/visibility/whatever) — SectionTabList only lays it out, it does
    # not manage its content. A general "status widget" slot any current or
    # future section can use, not Notification-specific — added 2026-08-03.
    trailing_widget_factory: Callable[[], QWidget] | None = None
    # Optional: given the constructed page and a UICommandService, connect
    # whatever signals the page needs wired to app-level services (sidebar
    # status line, cross-section navigation) — lets a plugin page react to
    # generic MainWindow services without MainWindow importing the page's
    # specific type. See interface/main_window.py's __init__.
    wire: Callable[[QWidget, "UICommandService"], None] | None = None


class SectionRegistry(KeyedOrderedRegistry[SectionSpec]):
    """Open, ordered replacement for the old closed SectionKey enum — every
    section is its own full-width top-level view in MainWindow.view_stack,
    switched to via Sidebar's SectionTabList; both built-in and
    plugin-provided sections register into the same collection.
    register()/ordered()/keys() come from KeyedOrderedRegistry
    (interface/registry_base.py) — keys() specifically is used by
    launcher.py to diff before/after a single plugin's register(api) call
    and learn which section(s) that plugin contributed, for per-repo
    Plugin gating."""

    def __init__(self) -> None:
        super().__init__(label="Section")
