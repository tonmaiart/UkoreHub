"""Root-path detection: rooted at the active UkoreHub repo, falling back to
Maya's own current workspace when UkoreHub has no active repo (e.g. Maya was
opened outside of UkoreHub, or no repo has been selected yet)."""

from __future__ import annotations

from pathlib import Path


def find_ukorehub_root() -> Path:
    """Locate the UkoreHub install root from this file's own position on disk.

    This file lives at
    plugins/studio/maya_launcher/UkoreBrowser/maya-scripts/UkoreBrowser/core/repo_context.py
    — seven parents up is the UkoreHub repo root. Works without any IPC
    because this tool's own files are physically inside the UkoreHub
    install; the same trick the old code used (deriving its own template/
    folder from UkoreBrowser.__file__), just extended further.
    """
    return Path(__file__).resolve().parents[7]


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


def get_root_path() -> str:
    """The browser's root: the active UkoreHub repo, else Maya's current
    workspace directory. Deliberately NOT the current scene file's folder —
    the Miller-column project/class/scene/shot/element lists are built
    relative to this root, and rooting at the scene's own (usually leaf,
    subfolder-less) folder left them permanently empty."""
    repo_path = get_active_repo_path()
    if repo_path is not None:
        return repo_path

    import maya.cmds as cmds

    return cmds.workspace(q=True, rd=True)


def get_initial_browse_path(root_path: str) -> str:
    """Where the browser should land on open: the current Maya scene
    file's folder if one is open and it's actually inside root_path (so
    you start out where you're working), else root_path itself."""
    from UkoreBrowser.core.maya_ops import get_current_scene_path

    scene_path = get_current_scene_path()
    if scene_path:
        scene_dir = Path(scene_path).parent
        try:
            scene_dir.relative_to(root_path)
        except ValueError:
            return root_path
        if scene_dir.is_dir():
            return str(scene_dir)

    return root_path


def get_pipeline_root_tabs() -> list[dict]:
    """Root-path tab options for the browser's top tab bar: the active
    repo itself, plus every repo declared as a pipeline input/output for it
    in plugins/studio/pipeline_architect's shared config
    (data/plugins/studio/pipeline_architect.json). Read directly off disk,
    same reason get_active_repo_path() constructs its own stores — Maya's
    Python has no PluginAPI instance to call plugin_config_store() through.
    Returns [] if there's no active repo. Each item:
    {"label": str, "path": str}."""
    try:
        root = find_ukorehub_root()
        from core.extensibility.config_store import PluginConfigStore
        from core.paths import resolve_repo_path
        from core.store import LocalConfigStore, MetadataStore

        local_config = LocalConfigStore(root / "data" / "local_config.json")
        project_id = local_config.active_project_id
        repo_id = local_config.active_repo_id
        if not (local_config.workspace_root and project_id and repo_id):
            return []

        store = MetadataStore(root / "data" / "projects.json")
        active_project = store.get_project(project_id)
        active_repo = store.get_repo(project_id, repo_id)
        active_path = resolve_repo_path(local_config.workspace_root, active_project.name, active_repo.name)
        if not active_path.is_dir():
            return []

        tabs = [{"label": active_repo.name, "path": str(active_path)}]

        pipeline_store = PluginConfigStore(root / "data" / "plugins" / "studio" / "pipeline_architect.json")
        entry = pipeline_store.get("projects", {}).get(project_id, {}).get("repos", {}).get(repo_id, {})

        def _add_refs(refs, prefix):
            for ref in refs:
                try:
                    ref_project = store.get_project(ref["project_id"])
                    ref_repo = store.get_repo(ref["project_id"], ref["repo_id"])
                    ref_path = resolve_repo_path(local_config.workspace_root, ref_project.name, ref_repo.name)
                except Exception:
                    continue
                if ref_path.is_dir():
                    tabs.append({"label": "{} {}".format(prefix, ref_repo.name), "path": str(ref_path)})

        _add_refs(entry.get("pipeline_inputs", []), "In:")
        _add_refs(entry.get("pipeline_outputs", []), "Out:")

        return tabs
    except Exception:
        return []
