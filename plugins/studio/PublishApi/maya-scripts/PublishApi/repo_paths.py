"""Publish-destination resolution — always UkoreHub's own active-repo
pipeline metadata (Project Editor's declared pipeline connections), never a
filesystem-path convention like the old '.../share/...' -> '.../publish/...'
string swap ModelPublisher/RigPublisher/AnimationPublisher used to each
carry their own copy of. This is the single source of truth all three of
those plugins (and UkoreBrowser) resolve a publish root through.

As of 2026-07-19, Project Editor only has ONE kind of pipeline connection
("Connect Pipeline Input Path...", stored under a repo's own
"pipeline_inputs" entry) — there's no separate "pipeline outputs" concept
to distinguish anymore (see plugins/studio/project_editor/README.md for
why). Functions/parameters here still talk about "output" from a
Publisher plugin's own point of view (the destination it publishes into),
since that's still what get_publish_root() resolves — it's just reading
the same unified "pipeline_inputs" list Project Editor now stores
everything in, not a distinct "pipeline_outputs" one."""

from __future__ import annotations

from pathlib import Path


def find_ukorehub_root() -> Path:
    """Locate the UkoreHub install root from this file's own position on
    disk. This file lives at
    plugins/studio/PublishApi/maya-scripts/PublishApi/repo_paths.py — five
    parents up is the UkoreHub repo root. Works without any IPC because
    this tool's own files are physically inside the UkoreHub install, the
    same trick plugins/studio/UkoreBrowser/.../core/repo_context.py uses
    (that one needs parents[6] instead — it has an extra core/ subfolder
    between the package root and this same kind of file)."""
    return Path(__file__).resolve().parents[5]


def get_active_repo():
    """(project, repo, repo_path) for whichever repo is currently active in
    UkoreHub, or (None, None, None) if there isn't one (no workspace
    configured, no active repo selected, or the repo/project record no
    longer exists). Constructs its own stores straight off disk — Maya's
    Python has no PluginAPI instance to call plugin_config_store()/
    api.metadata through."""
    root = find_ukorehub_root()
    from core.store import LocalConfigStore, MetadataStore

    local_config = LocalConfigStore(root / "data" / "local_config.json")
    project_id = local_config.active_project_id
    repo_id = local_config.active_repo_id
    if not (local_config.workspace_root and project_id and repo_id):
        return None, None, None

    from core.exceptions import NotFoundError

    store = MetadataStore(root / "data" / "projects.json")
    try:
        project = store.get_project(project_id)
        repo = store.get_repo(project_id, repo_id)
    except NotFoundError:
        return None, None, None

    repo_path = Path(local_config.workspace_root) / repo.local_path
    return project, repo, repo_path


def get_pipeline_refs() -> list[dict]:
    """Every {"project_id", "repo_id", "custom_path_id"} pipeline
    connection the active repo has made via "Connect Pipeline Input
    Path..." in Project Editor, read directly off
    plugins/studio/project_editor's shared PluginConfigStore file — same
    "construct the store straight off disk" approach get_active_repo()
    uses above, and the same one
    plugins/studio/UkoreBrowser/.../core/repo_context.py's
    get_pipeline_root_tabs() already relies on. Returns [] if there's no
    active repo."""
    root = find_ukorehub_root()
    from core.extensibility.config_store import PluginConfigStore

    project, repo, _ = get_active_repo()
    if project is None:
        return []

    pipeline_store = PluginConfigStore(root / "data" / "plugins" / "studio" / "project_editor.json")
    entry = pipeline_store.get("projects", {}).get(project.id, {}).get("repos", {}).get(repo.id, {})
    return entry.get("pipeline_inputs", [])


def resolve_ref(ref: dict):
    """Resolves a {"project_id", "repo_id", ...} pipeline ref (as returned
    by get_pipeline_refs) to (project, repo, repo_path), or None if the
    project/repo record no longer exists. `repo_path` is not guaranteed to
    exist on disk (the repo may not be cloned locally yet) — callers
    should check `repo_path.is_dir()` themselves if that matters."""
    root = find_ukorehub_root()
    from core.exceptions import NotFoundError
    from core.store import LocalConfigStore, MetadataStore

    local_config = LocalConfigStore(root / "data" / "local_config.json")
    store = MetadataStore(root / "data" / "projects.json")
    try:
        project = store.get_project(ref["project_id"])
        repo = store.get_repo(ref["project_id"], ref["repo_id"])
    except NotFoundError:
        return None
    repo_path = Path(local_config.workspace_root) / repo.local_path
    return project, repo, repo_path


def get_custom_paths(project_id: str, repo_id: str) -> list[dict]:
    """Every CustomPath dict ({"id", "label", "path"}) the given repo has
    declared for itself (see plugins/studio/project_editor's
    custom_paths_settings_page.py) — read directly off project_editor's
    shared PluginConfigStore file, same approach get_pipeline_refs() uses."""
    root = find_ukorehub_root()
    from core.extensibility.config_store import PluginConfigStore

    pipeline_store = PluginConfigStore(root / "data" / "plugins" / "studio" / "project_editor.json")
    entry = pipeline_store.get("projects", {}).get(project_id, {}).get("repos", {}).get(repo_id, {})
    return entry.get("custom_paths", [])


def get_custom_path(project_id: str, repo_id: str, custom_path_id: str | None) -> dict | None:
    """Looks up one of `repo_id`'s declared CustomPath entries by id —
    None if custom_path_id is falsy or no longer exists (e.g. it was
    removed after some pipeline ref was already pointed at it, or after a
    tool's Repo Studio Setting already chose it)."""
    if not custom_path_id:
        return None
    for custom_path in get_custom_paths(project_id, repo_id):
        if custom_path["id"] == custom_path_id:
            return custom_path
    return None


def get_chosen_output_ref(tool_id: str) -> dict | None:
    """The pipeline connection a studio admin picked as `tool_id`'s
    publish destination on the active repo, via that tool's own Repo
    Studio Setting tab (e.g. plugins/studio/ModelPublisher's
    ModelPublisherSettingsPage) — read directly off that tool's own
    PluginConfigStore file (data/plugins/studio/<tool_id>.json), same
    "construct the store straight off disk" approach every function here
    uses. None if nothing has been chosen yet for this repo
    (get_publish_root falls back to "the repo's only declared
    connection" in that case, if unambiguous)."""
    root = find_ukorehub_root()
    from core.extensibility.config_store import PluginConfigStore

    project, repo, _ = get_active_repo()
    if project is None:
        return None

    tool_store = PluginConfigStore(root / "data" / "plugins" / "studio" / f"{tool_id}.json")
    key = f"{project.id}:{repo.id}"
    return tool_store.get("repo_publish_target", {}).get(key)


def get_publish_root(tool_id: str) -> str:
    """The publish destination root `tool_id` (e.g. "model_publisher")
    builds its output path under, for whichever repo is currently active
    in Maya — the chosen pipeline connection's target repo path, joined
    with its chosen CustomPath's own relative path.

    Resolution order:
    1. If a studio admin has explicitly chosen one of the active repo's
       pipeline connections for this specific tool (get_chosen_output_ref),
       use that.
    2. Else, if the active repo has exactly ONE declared pipeline
       connection, use it — no ambiguity to resolve, so the common case
       needs no per-tool configuration at all.
    3. Else, raise: multiple pipeline connections exist and none has been
       chosen for this tool yet.

    Raises RuntimeError with a human-readable reason in every failure case
    (no active repo, no pipeline connection declared, ambiguous choice,
    target repo not cloned yet, chosen CustomPath no longer exists) rather
    than returning None/falling back to anything else — callers (each
    Publisher plugin's function.py) should catch this and show the
    message to the artist directly."""
    project, repo, _ = get_active_repo()
    if project is None:
        raise RuntimeError(
            "No active repo selected in UkoreHub. Open UkoreHub, pick a project/repo, then try again."
        )

    connections = get_pipeline_refs()
    if not connections:
        raise RuntimeError(
            "'{}' has no pipeline connection declared in Project Editor. "
            "Add one under Repository Setting > Custom Paths > Connect Input Path... "
            "before publishing.".format(repo.name)
        )

    ref = get_chosen_output_ref(tool_id)
    if ref is None:
        if len(connections) == 1:
            ref = connections[0]
        else:
            raise RuntimeError(
                "'{}' has {} pipeline connections declared and none is chosen for this tool yet. "
                "Pick one under Repository Setting's Repo Studio Setting tab for this tool.".format(
                    repo.name, len(connections)
                )
            )

    resolved = resolve_ref(ref)
    if resolved is None:
        raise RuntimeError(f"'{repo.name}'s chosen pipeline connection's target repo no longer exists.")
    _target_project, target_repo, target_repo_path = resolved

    if not target_repo_path.is_dir():
        raise RuntimeError(
            f"Pipeline connection target repo '{target_repo.name}' hasn't been cloned yet — clone it in UkoreHub first."
        )

    custom_path = get_custom_path(ref["project_id"], ref["repo_id"], ref.get("custom_path_id"))
    if custom_path is None:
        raise RuntimeError(
            f"'{target_repo.name}'s declared Custom Path for this pipeline connection no longer exists — "
            "re-pick a target under Repository Setting's Repo Studio Setting tab for this tool."
        )

    return str(target_repo_path / custom_path["path"])
