"""Shared file-write helpers for every JSON store in core/storage/ and
core/extensibility/config_store.py — one atomic-write implementation
instead of each store hand-rolling its own."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp_path, path)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
