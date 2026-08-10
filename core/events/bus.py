"""Generic in-memory event bus — base for core/events/debug_log.py's
DebugLogBus. Owned by
core/app_core.py's UkoreCore (core.debug_bus), not a
module-level global — a caller reaches it via a core/api handle instead
of a bare import.

Not a QObject — stays Qt-free like the rest of core/; every consumer today
subscribes with a plain Python callback and runs on the main Qt thread
already, so there's no cross-thread safety concern in practice."""
from __future__ import annotations

from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class InMemoryEventBus(Generic[T]):
    def __init__(self, max_entries: int = 500):
        self._max_entries = max_entries
        self._entries: list[T] = []
        self._listeners: list[Callable[[T], None]] = []

    def push(self, entry: T) -> T:
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)
        for listener in list(self._listeners):
            listener(entry)
        return entry

    def entries(self) -> list[T]:
        return list(self._entries)

    def add_listener(self, callback: Callable[[T], None]) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[T], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def clear(self) -> None:
        self._entries.clear()
