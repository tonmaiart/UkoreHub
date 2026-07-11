from __future__ import annotations

import re
from pathlib import Path

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_folder_name(name: str) -> str:
    cleaned = _INVALID_CHARS.sub("_", name).strip().strip(".")
    return cleaned or "unnamed"


def resolve_repo_path(workspace_root: str | Path, project_name: str, repo_name: str) -> Path:
    return Path(workspace_root) / sanitize_folder_name(project_name) / sanitize_folder_name(repo_name)
