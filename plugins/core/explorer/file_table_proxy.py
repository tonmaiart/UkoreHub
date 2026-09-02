from __future__ import annotations

from datetime import datetime

from plugin_api import format_relative_datetime


def format_time_ago(dt: datetime) -> str:
    return format_relative_datetime(dt)
