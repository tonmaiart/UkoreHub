from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from plugin_api.registries.registry_base import KeyedOrderedRegistry


@dataclass(frozen=True)
class NotificationSpec:
    key: str
    order: int
    # Constructs (or returns an already-constructed) widget to place as a
    # row in Sidebar's listWidget_notification — called once, at MainWindow
    # construction time. Same eagerly-constructed-then-lambda-returns-it
    # shape as SectionSpec.page_factory/SidebarFooterActionSpec.widget_factory.
    widget_factory: Callable[[], QWidget]
    # Optional: given the constructed widget, return any background QThread
    # workers it owns, so MainWindow.closeEvent can terminate them safely —
    # mirrors SidebarFooterActionSpec.background_threads.
    background_threads: Callable[[QWidget], list] | None = None


class NotificationRegistry(KeyedOrderedRegistry[NotificationSpec]):
    """Open, ordered collection of widgets contributed into
    listWidget_notification — lets any plugin add its own notification row
    without MainWindow hardcoding it. register()/ordered()/keys() come from
    KeyedOrderedRegistry (plugin_api/registries/registry_base.py)."""

    def __init__(self) -> None:
        super().__init__(label="Notification")
