from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QWidget

from core.exceptions import ValidationError


@dataclass(frozen=True)
class SectionHost:
    """Passed to SectionSpec.wire(page, host). A fixed, small set of named
    callbacks — not a generic event bus — mirroring background_threads'
    shape below: MainWindow invokes wire() generically, the closure reaches
    into the page's own internals. Add a new named field only on
    demonstrated need, not speculatively."""

    set_status_message: Callable[[str], None]
    navigate_and_focus: Callable[[str, Path], None]


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
    # Optional: given the constructed page and a SectionHost, connect
    # whatever signals the page needs wired to app-level services (sidebar
    # status line, cross-section navigation) — lets a plugin page react to
    # generic MainWindow services without MainWindow importing the page's
    # specific type. See interface/main_window.py's __init__.
    wire: Callable[[QWidget, "SectionHost"], None] | None = None


class SectionRegistry:
    """Open, ordered replacement for the old closed SectionKey enum — every
    section is its own full-width top-level view in MainWindow.view_stack,
    switched to via Sidebar's SectionTabList; both built-in and
    plugin-provided sections register into the same collection."""

    def __init__(self) -> None:
        self._specs: dict[str, SectionSpec] = {}

    def register(self, spec: SectionSpec) -> None:
        if spec.key in self._specs:
            raise ValidationError(f"Section key '{spec.key}' is already registered")
        self._specs[spec.key] = spec

    def ordered(self) -> list[SectionSpec]:
        return sorted(self._specs.values(), key=lambda spec: (spec.order, spec.key))
