from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from core.models import Project, Repo

# Three small, single-method Protocols instead of one combined one — a
# page implements any subset of these (see main_window.py's three call
# sites, isinstance-checked independently), never all three at once. A
# single Protocol with all three methods would require isinstance() to
# see every one of them before matching, which would break every page
# that only implements one (e.g. Explorer's RepoBrowserPage implements
# set_repo + browse_to_path but not sync_active_repo).
#
# These stay optional-per-page on purpose: making any of them mandatory
# was tried and reverted after it crashed pages with no notion of "active
# repo" (DebugConsole, BananaSketch) — see
# developer/bug-history/2026-08-09-set-repo-not-optional-protocol-method.md.
# A page satisfies a Protocol just by having the right method (structural
# typing, PEP 544) — it never needs to inherit from these classes.


@runtime_checkable
class SetRepoPage(Protocol):
    """Wants to know when the active repo changes — called whenever this
    page becomes the visible view_stack page (interface/main_window.py's
    _apply_to_current_page) and at startup/on explicit repo switches."""

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None: ...


@runtime_checkable
class PathFocusablePage(Protocol):
    """Can jump straight to and highlight a specific file — called by
    interface/main_window.py's _navigate_and_focus (SectionHost.navigate_and_focus)
    when another section asks to "show this file over there" (e.g. Submit's
    "Inspect in Explorer")."""

    def browse_to_path(self, path: Path) -> None: ...


@runtime_checkable
class AutoSyncPage(Protocol):
    """Wants to run its own clone/pull when the app auto-syncs the active
    repo — called by interface/main_window.py's _start_auto_sync on every
    "Select Repo..." pick and app launch, for every registered page that
    implements it (today, just Submit)."""

    def sync_active_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None: ...
