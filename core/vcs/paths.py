from __future__ import annotations

import re
from pathlib import Path

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_folder_name(name: str) -> str:
    cleaned = _INVALID_CHARS.sub("_", name).strip().strip(".")
    return cleaned or "unnamed"


def extract_git_repo_name(git_url: str) -> str:
    """Derives the on-disk folder name from a git remote URL — the last
    path segment, minus a trailing '.git' — so the clone folder always
    matches the actual git remote regardless of what display Name the user
    later gives the Repo/CatalogEntry. Handles both HTTPS
    ('https://github.com/org/Repo.git') and SSH ('git@github.com:org/Repo.git')
    remotes."""
    cleaned = git_url.strip().replace("\\", "/").rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    last_part = cleaned.split("/")[-1]
    if ":" in last_part:
        last_part = last_part.split(":")[-1]
    return sanitize_folder_name(last_part)


def resolve_repo_path(workspace_root: str | Path, project_name: str, repo_name_or_git_url: str) -> Path:
    if repo_name_or_git_url.startswith(("http://", "https://", "git@")):
        folder_name = extract_git_repo_name(repo_name_or_git_url)
    else:
        folder_name = sanitize_folder_name(repo_name_or_git_url)
    return Path(workspace_root) / sanitize_folder_name(project_name) / folder_name
