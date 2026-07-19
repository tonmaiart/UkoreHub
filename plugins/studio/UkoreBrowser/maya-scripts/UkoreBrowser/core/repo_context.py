"""Root-path detection: rooted at the active UkoreHub repo, falling back to
Maya's own current workspace when UkoreHub has no active repo (e.g. Maya was
opened outside of UkoreHub, or no repo has been selected yet).

Path/pipeline-metadata resolution itself goes through PublishApi
(plugins/studio/PublishApi/maya-scripts/PublishApi/repo_paths.py) as of
2026-07-19, instead of this file carrying its own duplicate copy of
find_ukorehub_root()/store construction — so UkoreBrowser and the
Publisher plugins (ModelPublisher/RigPublisher/AnimationPublisher) share
exactly one source of truth for what the active repo/pipeline metadata is.
See that plugin's README."""

from __future__ import annotations

from pathlib import Path

from PublishApi import repo_paths as publish_api_repo_paths


def get_active_repo_path() -> str | None:
    """Absolute path to the repo UkoreHub currently has active, or None if
    there isn't one (no workspace configured, no active repo selected, the
    repo folder doesn't exist on disk, or PublishApi isn't importable yet
    — e.g. this plugin's PYTHONPATH contribution hasn't taken effect)."""
    try:
        _project, _repo, repo_path = publish_api_repo_paths.get_active_repo()
        if repo_path is None or not repo_path.is_dir():
            return None
        return str(repo_path)
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


def _ref_key(ref: dict) -> str:
    """Same compound-key format plugins/studio/UkoreBrowser/settings_page.py
    uses for its Repo Studio Setting checkbox list — a ref has no id of
    its own, so (target project, target repo, target CustomPath) together
    identify one specific pipeline connection."""
    return "{}:{}:{}".format(ref.get("project_id"), ref.get("repo_id"), ref.get("custom_path_id"))


def _get_hidden_root_tab_keys(project_id: str, repo_id: str) -> set[str]:
    """The set of ref keys a studio admin has hidden from the root-tab row
    for this repo, via UkoreBrowser's own Repo Studio Setting tab — read
    directly off this plugin's own PluginConfigStore file
    (data/plugins/studio/ukore_browser.json), same "construct the store
    straight off disk" approach every function in this module family
    uses (Maya's Python has no PluginAPI instance to go through)."""
    root = publish_api_repo_paths.find_ukorehub_root()
    from core.extensibility.config_store import PluginConfigStore

    tool_store = PluginConfigStore(root / "data" / "plugins" / "studio" / "ukore_browser.json")
    hidden = tool_store.get("repo_hidden_root_tabs", {}).get(f"{project_id}:{repo_id}", [])
    return set(hidden)


def get_pipeline_root_tabs() -> list[dict]:
    """Root-path tab options for the browser's top tab bar: the active
    repo itself, plus every repo it has connected to via "Connect
    Pipeline Input Path..." in Project Editor (via
    PublishApi.repo_paths.get_pipeline_refs/resolve_ref/get_custom_path),
    each resolved down to its specific declared CustomPath rather than
    just the target repo's root — minus whichever ones a studio admin has
    hidden via this plugin's own Repo Studio Setting tab
    (_get_hidden_root_tab_keys above). Returns [] if there's no active
    repo. Each item: {"label": str, "path": str}."""
    try:
        project, repo, repo_path = publish_api_repo_paths.get_active_repo()
        if project is None or repo_path is None or not repo_path.is_dir():
            return []

        tabs = [{"label": repo.name, "path": str(repo_path)}]
        hidden_keys = _get_hidden_root_tab_keys(project.id, repo.id)

        for ref in publish_api_repo_paths.get_pipeline_refs():
            if _ref_key(ref) in hidden_keys:
                continue
            resolved = publish_api_repo_paths.resolve_ref(ref)
            if resolved is None:
                continue
            _ref_project, ref_repo, ref_repo_path = resolved
            custom_path = publish_api_repo_paths.get_custom_path(
                ref["project_id"], ref["repo_id"], ref.get("custom_path_id")
            )
            if custom_path is None:
                continue
            ref_path = ref_repo_path / custom_path["path"]
            if ref_path.is_dir():
                tabs.append({"label": "{} — {}".format(ref_repo.name, custom_path["label"]), "path": str(ref_path)})

        return tabs
    except Exception:
        return []
