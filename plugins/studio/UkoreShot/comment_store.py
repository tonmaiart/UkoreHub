from __future__ import annotations

import json
from pathlib import Path

_SUFFIX = ".ukoreshot.json"


def sidecar_path(video_path: Path) -> Path:
    return video_path.with_name(video_path.name + _SUFFIX)


def load(video_path: Path) -> dict:
    """{"frames": {"<frame_index>": {"strokes": [...], "note": "..."}}} —
    saved next to the video itself in the resolved library folder (see
    video_path_store.resolve_video_root) so it travels with the shared
    library, no separate app data store needed. Returns {"frames": {}} if
    no sidecar exists yet, or it fails to parse (a corrupt/foreign file
    next to a video shouldn't crash the viewer)."""
    path = sidecar_path(video_path)
    if not path.is_file():
        return {"frames": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"frames": {}}
    if not isinstance(data, dict) or not isinstance(data.get("frames"), dict):
        return {"frames": {}}
    return data


def save(video_path: Path, frames: dict) -> None:
    path = sidecar_path(video_path)
    path.write_text(json.dumps({"frames": frames}, indent=2), encoding="utf-8")
