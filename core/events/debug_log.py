"""In-memory debug log bus — see core/events/bus.py's InMemoryEventBus.
Owned by core/app_core.py's UkoreCore (core.debug_bus) and reached via a
core/api handle rather than a bare module import. Consumed by
plugins/core/DebugConsole/'s live viewer page. Deliberately not persisted
(see DebugConsole's own README) and capped at 1000 entries by default."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field

from core.events.bus import InMemoryEventBus


@dataclass
class DebugLogEntry:
    source: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().strftime("%H:%M:%S"))


class DebugLogBus(InMemoryEventBus[DebugLogEntry]):
    def __init__(self, max_entries: int = 1000):
        super().__init__(max_entries=max_entries)
        self._sources: set[str] = set()

    def register_source(self, source: str) -> None:
        """Declares a named log channel so it shows up in DebugConsole's source
        filter even before the first log() call — optional (log() auto-
        registers too) but makes a plugin's intent to use this explicit."""
        self._sources.add(source)

    def log(self, source: str, message: str) -> DebugLogEntry:
        self._sources.add(source)
        return self.push(DebugLogEntry(source=source, message=message))

    def sources(self) -> list[str]:
        return sorted(self._sources)
