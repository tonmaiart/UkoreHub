"""In-memory notification bus — see core/events/bus.py's InMemoryEventBus.
Owned by core/app_core.py's UkoreCore (core.notification_bus) and reached
via a core/api handle rather than a bare module import. Consumed by
plugins/core/Notification/'s tab. Deliberately not persisted (a
notification's on_click is a live Python callback, which can't survive an
app restart anyway) and capped at 500 entries by default."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from core.events.bus import InMemoryEventBus


@dataclass
class NotificationEntry:
    source: str
    project_id: str
    # None means "applies to every repo in the project" — the producer's
    # scope choice at push time; the Notification page auto-filters by
    # whichever repo is currently active, with no user-facing toggle.
    repo_id: str | None
    label: str
    icon_path: Path | None = None
    # Raw image bytes (e.g. a GitHub avatar already downloaded by the
    # producer) — takes priority over icon_path in NotificationCard, since
    # it needs no filesystem round-trip and isn't tied to a static icon file.
    icon_bytes: bytes | None = None
    on_click: Callable[[], None] | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


class NotificationBus(InMemoryEventBus[NotificationEntry]):
    def push(
        self,
        source: str,
        project_id: str,
        repo_id: str | None,
        label: str,
        *,
        icon_path: Path | None = None,
        icon_bytes: bytes | None = None,
        on_click: Callable[[], None] | None = None,
    ) -> NotificationEntry:
        entry = NotificationEntry(
            source=source,
            project_id=project_id,
            repo_id=repo_id,
            label=label,
            icon_path=icon_path,
            icon_bytes=icon_bytes,
            on_click=on_click,
        )
        return super().push(entry)

    def entries_for(self, project_id: str, repo_id: str | None) -> list[NotificationEntry]:
        """Every entry visible for this project/repo — project-wide entries
        (repo_id=None) plus entries scoped to this specific repo_id — newest
        first. Pure filtering logic, safe to unit test without Qt."""
        visible = [e for e in self.entries() if e.project_id == project_id and (e.repo_id is None or e.repo_id == repo_id)]
        return sorted(visible, key=lambda e: e.timestamp, reverse=True)
