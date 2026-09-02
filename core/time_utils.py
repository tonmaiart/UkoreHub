"""Relative-time formatting shared by every "N ago" display in the app
(commit history, plugin last-checked time, file modified time). Pure
datetime logic, no Qt.
"""
from __future__ import annotations

from datetime import datetime, timezone


def parse_iso_datetime(raw: str) -> datetime | None:
    """Parses a git/GitHub-style ISO datetime string (handles a trailing
    "Z"), defaulting to UTC when the string carries no offset. Returns
    None on empty input or a parse failure."""
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def format_relative_datetime(dt: datetime) -> str:
    """"just now" / "N min(s) ago" / "N hour(s) ago" / "N day(s) ago" /
    "N month(s) ago" / "N year(s) ago" for an already-resolved datetime.
    Works with both naive (e.g. local file mtime) and timezone-aware
    (e.g. parse_iso_datetime's output) input."""
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    seconds = max(0, (now - dt).total_seconds())
    if seconds < 60:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} min{'s' if minutes != 1 else ''} ago"
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = int(hours // 24)
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''} ago"
    months = int(days // 30)
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''} ago"
    years = int(days // 365)
    return f"{years} year{'s' if years != 1 else ''} ago"
