"""In-memory, cross-plugin debug log bus — any plugin/add-on/core module can
call log(source, message) from anywhere at runtime (not just inside
register(api), unlike most of PluginAPI's registries), no `api` handle
needed, same "construct/reach directly, convention not import" spirit
PluginConfigStore already uses elsewhere in this codebase. Consumed by
plugins/studio/DebugConsole/'s live viewer page. Deliberately not
persisted (see DebugConsole's own README) and not a QObject — this module
stays Qt-free like the rest of core/extensibility/; DebugConsolePage
subscribes with a plain Python callback and is responsible for its own UI
thread-safety (fine in practice: every call in this app happens on the
main Qt thread already, there is no background-thread producer today)."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Callable

_MAX_ENTRIES = 1000


@dataclass
class DebugLogEntry:
    source: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().strftime("%H:%M:%S"))


_entries: list[DebugLogEntry] = []
_sources: set[str] = set()
_listeners: list[Callable[[DebugLogEntry], None]] = []


def register_source(source: str) -> None:
    """Declares a named log channel so it shows up in DebugConsole's source
    filter even before the first log() call — optional (log() auto-
    registers too) but makes a plugin's intent to use this explicit."""
    _sources.add(source)


def log(source: str, message: str) -> None:
    _sources.add(source)
    entry = DebugLogEntry(source=source, message=message)
    _entries.append(entry)
    if len(_entries) > _MAX_ENTRIES:
        _entries.pop(0)
    for listener in list(_listeners):
        listener(entry)


def entries() -> list[DebugLogEntry]:
    return list(_entries)


def sources() -> list[str]:
    return sorted(_sources)


def add_listener(callback: Callable[[DebugLogEntry], None]) -> None:
    _listeners.append(callback)


def remove_listener(callback: Callable[[DebugLogEntry], None]) -> None:
    if callback in _listeners:
        _listeners.remove(callback)


def clear() -> None:
    _entries.clear()
