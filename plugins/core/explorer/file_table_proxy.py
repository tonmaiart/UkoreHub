from __future__ import annotations

from datetime import datetime


def format_time_ago(dt: datetime) -> str:
    seconds = (datetime.now() - dt).total_seconds()
    if seconds < 60:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} min ago"
    hours = int(seconds // 3600)
    if hours < 24:
        return f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"
    days = int(seconds // 86400)
    if days < 30:
        return f"{days} day ago" if days == 1 else f"{days} days ago"
    months = int(seconds // 2592000)
    if months < 12:
        return f"{months} month ago" if months == 1 else f"{months} months ago"
    years = int(seconds // 31536000)
    return f"{years} year ago" if years == 1 else f"{years} years ago"
