from __future__ import annotations

import uuid
from dataclasses import dataclass

from plugin_api import MetadataStore, NotFoundError, Repo

# This plugin's id, also its Repo.plugin_data key (core/models.py's Repo) —
# each repo's own pipeline_inputs/custom_paths live at
# repo.plugin_data["project_editor"], not in a separate PluginConfigStore
# file, since the data is always scoped to exactly one (project_id, repo_id)
# pair. See README.md for the exact shape and how another plugin should
# read it, and _migrate_legacy_data below for the one-time cutover from the
# old data/plugins/core/project_editor.json blob.
# There used to also be a "pipeline_outputs" key (a separate, independently
# curated list) — removed 2026-07-19 when "Set as Pipeline Output..." was
# removed from ProjectGraphView's node context menu in favor of a single
# unified "Connect Pipeline Input Path..." action; every connection a repo
# makes is a "pipeline_inputs" entry now, regardless of whether the real
# data flow is "I publish into this" or "I read from this".
PLUGIN_ID = "project_editor"
_LEGACY_PROJECTS_KEY = "projects"


@dataclass
class CustomPath:
    """One named location a repo exposes for other repos' pipeline refs to
    connect to — e.g. RigPublish might declare "Character" -> "Character"
    and "Prop" -> "Prop", each a subfolder relative to RigPublish's own
    repo root. Added 2026-07-19 alongside RepoRef.custom_path_id: a
    pipeline ref used to point at a whole target repo; it now points at
    one specific declared location within it, since a single shared
    "...Publish" repo is rarely one undifferentiated dumping ground in
    practice. `id` is a stable uuid4 (not derived from `label`) so
    renaming a custom path doesn't invalidate every RepoRef that already
    points at it."""

    id: str
    label: str
    path: str

    def to_dict(self) -> dict:
        return {"id": self.id, "label": self.label, "path": self.path}

    @classmethod
    def from_dict(cls, data: dict) -> "CustomPath":
        return cls(id=data["id"], label=data["label"], path=data["path"])

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex


@dataclass
class RepoRef:
    """A (project_id, repo_id) pair plus, as of 2026-07-19, which of the
    target repo's declared CustomPath entries this specific reference
    points at — every cross-repo reference in this codebase is stored as
    a (project_id, repo_id) pair rather than a bare repo id
    (local_config_store.active_project_id/active_repo_id, RepoPickerDialog's
    own return shape), since MetadataStore.get_repo(project_id, repo_id)
    always needs both regardless of whether Repo.id UUIDs happen to be
    globally unique.

    `custom_path_id=None` means "no custom path chosen yet" — only ever
    true for a RepoRef created before this field existed (backward
    compatibility for old data); every ref created through
    CustomPathsSettingsPage's "Connect Input Path" section (moved there
    2026-07-19 from ProjectGraphView's now-removed add_pipeline_ref) now
    requires picking one, since a repo can connect to the very same target
    repo more than once, each connection pointing at a different
    CustomPath (e.g. one to RigPublish's "Character" location, another to
    its "Prop" location) — something a bare (project_id, repo_id) pair
    alone couldn't distinguish.

    `direction` (added 2026-07-19) is purely cosmetic — it never affects
    ProjectGraphView._layout_nodes' level/row assignment, only which end
    of the drawn edge gets the arrowhead in ProjectGraphView.load_project:
    `"input"` (the default, matching every ref saved before this field
    existed) draws the arrow pointing INTO the repo that made this
    connection; `"output"` draws it pointing OUT of that repo toward the
    target repo it connected to instead."""

    project_id: str
    repo_id: str
    custom_path_id: str | None = None
    direction: str = "input"  # "input" | "output"

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "repo_id": self.repo_id,
            "custom_path_id": self.custom_path_id,
            "direction": self.direction,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RepoRef":
        return cls(
            project_id=data["project_id"],
            repo_id=data["repo_id"],
            custom_path_id=data.get("custom_path_id"),
            direction=data.get("direction", "input"),
        )


class PipelineStore:
    """Wraps each repo's own Repo.plugin_data["project_editor"] entry — one
    repo's declared pipeline connections ("Connect Pipeline Input Path...",
    each a RepoRef pointing at another repo's declared CustomPath), plus
    the repo's own declared CustomPath catalog (see that class). Rendered
    as directed edges between repo nodes in ProjectGraphView — see
    project_graph_view.py's _collect_edges. Named "inputs" (matching the
    node context menu's own "Connect Pipeline Input Path..." wording) even
    though a connection can represent either direction of real data flow
    — see RepoRef's docstring and this plugin's README for why the
    separate "outputs" concept was removed 2026-07-19."""

    def __init__(self, metadata_store: MetadataStore):
        self._metadata_store = metadata_store

    def get_inputs(self, project_id: str, repo_id: str) -> list[RepoRef]:
        entry = self._metadata_store.get_repo_plugin_data(project_id, repo_id, PLUGIN_ID)
        return [RepoRef.from_dict(d) for d in entry.get("pipeline_inputs", [])]

    def set_inputs(self, project_id: str, repo_id: str, refs: list[RepoRef]) -> None:
        self._set_field(project_id, repo_id, "pipeline_inputs", [ref.to_dict() for ref in refs])

    def get_custom_paths(self, project_id: str, repo_id: str) -> list[CustomPath]:
        entry = self._metadata_store.get_repo_plugin_data(project_id, repo_id, PLUGIN_ID)
        return [CustomPath.from_dict(d) for d in entry.get("custom_paths", [])]

    def get_custom_path(self, project_id: str, repo_id: str, custom_path_id: str | None) -> CustomPath | None:
        """Looks up one of a repo's declared CustomPath entries by id —
        the common lookup a RepoRef consumer needs (resolve what a
        pipeline ref's custom_path_id actually points at). Returns None
        if custom_path_id is None or no longer exists (e.g. it was
        deleted after some RepoRef was already pointed at it)."""
        if not custom_path_id:
            return None
        for custom_path in self.get_custom_paths(project_id, repo_id):
            if custom_path.id == custom_path_id:
                return custom_path
        return None

    def set_custom_paths(self, project_id: str, repo_id: str, custom_paths: list[CustomPath]) -> None:
        self._set_field(project_id, repo_id, "custom_paths", [cp.to_dict() for cp in custom_paths])

    def get_required_repos(self, project_id: str, repo_id: str) -> list[tuple[str, Repo]]:
        """Resolves this repo's own direct pipeline_inputs RepoRefs into the
        actual target Repo objects they point at — the set of repos that
        must exist on disk for this repo's pipeline connections to work.
        Deliberately direct-only: does NOT recurse into each target's own
        get_inputs, so a repo's requirements never cascade into its
        requirements' requirements — see ProjectGraphView.request_active_repo,
        the only caller, for why that matters (avoiding "clone the whole
        graph" from a single node click). Returns (project_id, Repo) pairs,
        not bare Repo, since a required target can live in a different
        Project than (project_id, repo_id) and Repo itself has no project_id
        field. Skips a ref pointing back at (project_id, repo_id) itself
        (malformed self-reference) and dedupes by (project_id, repo_id) —
        multiple CustomPath connections can target the same repo."""
        seen: set[tuple[str, str]] = set()
        required: list[tuple[str, Repo]] = []
        for ref in self.get_inputs(project_id, repo_id):
            key = (ref.project_id, ref.repo_id)
            if key == (project_id, repo_id) or key in seen:
                continue
            seen.add(key)
            try:
                target_repo = self._metadata_store.get_repo(ref.project_id, ref.repo_id)
            except NotFoundError:
                continue
            required.append((ref.project_id, target_repo))
        return required

    def _set_field(self, project_id: str, repo_id: str, field_name: str, value: list[dict]) -> None:
        entry = dict(self._metadata_store.get_repo_plugin_data(project_id, repo_id, PLUGIN_ID))
        entry[field_name] = value
        self._metadata_store.set_repo_plugin_data(project_id, repo_id, PLUGIN_ID, entry)


def migrate_legacy_data(api) -> None:
    """One-time cutover from the old data/plugins/core/project_editor.json
    PluginConfigStore blob into each repo's own Repo.plugin_data. Reading
    api.plugin_config_store pulls that blob fresh from the cloud; if its
    "projects" key is already empty, either nothing was ever stored there
    or a previous launch already migrated it (this clears the key once
    done) — either way there's nothing to do, making this safe to call on
    every register(), not just once."""
    legacy_store = api.plugin_config_store(PLUGIN_ID, shared=True)
    tree = legacy_store.get(_LEGACY_PROJECTS_KEY, {})
    if not tree:
        return
    for project_id, project_entry in tree.items():
        for repo_id, repo_entry in project_entry.get("repos", {}).items():
            data = {}
            if "pipeline_inputs" in repo_entry:
                data["pipeline_inputs"] = repo_entry["pipeline_inputs"]
            if "custom_paths" in repo_entry:
                data["custom_paths"] = repo_entry["custom_paths"]
            if not data:
                continue
            try:
                api.metadata.set_repo_plugin_data(project_id, repo_id, PLUGIN_ID, data)
            except NotFoundError:
                pass  # project/repo no longer exists — drop the stale entry
    legacy_store.set(_LEGACY_PROJECTS_KEY, {})
