from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from interface.registry_base import KeyedOrderedRegistry


@dataclass(frozen=True)
class SidebarFooterActionSpec:
    key: str
    order: int
    # Constructs (or returns an already-constructed) widget to place in
    # Sidebar's footer strip — called once, at Sidebar construction time.
    # See plugins/studio/self_updater/plugin.py for the eagerly-constructed-
    # then-lambda-returns-it pattern (same shape as SectionSpec.page_factory).
    widget_factory: Callable[[], QWidget]
    # Optional: given the constructed widget, return any background QThread
    # workers it owns, so MainWindow.closeEvent can terminate them safely —
    # mirrors SectionSpec.background_threads.
    background_threads: Callable[[QWidget], list] | None = None


class SidebarFooterActionRegistry(KeyedOrderedRegistry[SidebarFooterActionSpec]):
    """Open, ordered collection of widgets contributed into Sidebar's footer
    strip (sync status, account row, ...) — lets a plugin add a footer
    control (e.g. an Update button) without Sidebar hardcoding it.
    register()/ordered()/keys() come from KeyedOrderedRegistry
    (interface/registry_base.py)."""

    def __init__(self) -> None:
        super().__init__(label="Sidebar footer action")
