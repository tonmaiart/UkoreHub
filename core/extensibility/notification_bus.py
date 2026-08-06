"""In-memory, cross-plugin notification bus — the "socket" any plugin
calls directly to push a notification card, no `api` handle needed, same
"construct/reach directly, convention not import" spirit `debug_log.py` and
`PluginConfigStore` already use elsewhere in this codebase. Consumed by
plugins/core/Notification/'s tab. Deliberately not persisted (a
notification's on_click is a live Python callback, which can't survive an
app restart anyway) and not a QObject — stays Qt-free like the rest of
core/extensibility/; the one UI consumer is responsible for its own thread
safety (fine in practice: every push() in this app happens on the main Qt
thread already)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

_MAX_ENTRIES = 500


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


_entries: list[NotificationEntry] = []
_listeners: list[Callable[[NotificationEntry], None]] = []


def push(
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
    _entries.append(entry)
    if len(_entries) > _MAX_ENTRIES:
        _entries.pop(0)
    for listener in list(_listeners):
        listener(entry)
    return entry


def entries() -> list[NotificationEntry]:
    return list(_entries)


def entries_for(project_id: str, repo_id: str | None) -> list[NotificationEntry]:
    """Every entry visible for this project/repo — project-wide entries
    (repo_id=None) plus entries scoped to this specific repo_id — newest
    first. Pure filtering logic, safe to unit test without Qt."""
    visible = [e for e in _entries if e.project_id == project_id and (e.repo_id is None or e.repo_id == repo_id)]
    return sorted(visible, key=lambda e: e.timestamp, reverse=True)


def add_listener(callback: Callable[[NotificationEntry], None]) -> None:
    _listeners.append(callback)


def remove_listener(callback: Callable[[NotificationEntry], None]) -> None:
    if callback in _listeners:
        _listeners.remove(callback)


def clear() -> None:
    _entries.clear()
