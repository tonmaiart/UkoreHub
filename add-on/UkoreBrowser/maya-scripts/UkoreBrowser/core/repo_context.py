"""Root-path detection: rooted at the active UkoreHub repo, falling back to
Maya's own current workspace when UkoreHub has no active repo (e.g. Maya was
opened outside of UkoreHub, or no repo has been selected yet)."""

from __future__ import annotations

from pathlib import Path


def find_ukorehub_root() -> Path:
    """Locate the UkoreHub install root from this file's own position on disk.

    This file lives at
    add-on/UkoreBrowser/maya-scripts/UkoreBrowser/core/repo_context.py — five
    parents up is the UkoreHub repo root. Works without any IPC because this
    add-on's own files are physically inside the UkoreHub install; the same
    trick the old code used (deriving its own template/ folder from
    UkoreBrowser.__file__), just extended one more level.
    """
    return Path(__file__).resolve().parents[5]


def get_active_repo_path() -> str | None:
    """Absolute path to the repo UkoreHub currently has active, or None if
    there isn't one (no workspace configured, no active repo selected, the
    repo folder doesn't exist on disk, or `core` isn't importable — e.g. this
    add-on's PYTHONPATH contribution hasn't taken effect yet)."""
    try:
        root = find_ukorehub_root()
        from core.store import LocalConfigStore, MetadataStore
        from core.paths import resolve_repo_path

        local_config = LocalConfigStore(root / "data" / "local_config.json")
        if not (
            local_config.workspace_root
            and local_config.active_project_id
            and local_config.active_repo_id
        ):
            return None

        store = MetadataStore(root / "data" / "projects.json")
        project = store.get_project(local_config.active_project_id)
        repo = store.get_repo(local_config.active_project_id, local_config.active_repo_id)
        repo_path = resolve_repo_path(local_config.workspace_root, project.name, repo.name)

        return str(repo_path) if repo_path.is_dir() else None
    except Exception:
        return None


def get_start_path() -> str:
    """The path UkoreBrowser should open at: the current Maya scene file's
    folder if one is open (so the browser lands right where you're working),
    else the active UkoreHub repo, else Maya's current workspace directory."""
    from UkoreBrowser.core.maya_ops import get_current_scene_path

    scene_path = get_current_scene_path()
    if scene_path:
        scene_dir = Path(scene_path).parent
        if scene_dir.is_dir():
            return str(scene_dir)

    repo_path = get_active_repo_path()
    if repo_path is not None:
        return repo_path

    import maya.cmds as cmds

    return cmds.workspace(q=True, rd=True)
