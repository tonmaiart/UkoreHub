from __future__ import annotations

import uuid
from dataclasses import dataclass

from plugin_api import MetadataStore, NotFoundError, ProjectPluginConfigStore, Repo

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
_CATEGORIES_KEY = "categories"


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
class Category:
    """One named group a repo can be assigned to (added 2026-08-19 for the
    since-removed node graph's box-per-category layout; the graph is gone
    as of the 2026-08-19 list-view rewrite, but the assignment itself is
    still set via project_editor_page.py's "Assign Categories" button,
    dialogs.py's AssignCategoryDialog). Scoped to the whole Project rather
    than one repo — lives in
    Project.plugin_data["project_editor"]["categories"]
    (api.project_plugin_config_store(PLUGIN_ID), see PipelineStore.get_categories),
    not Repo.plugin_data, since the same category is shared across every
    repo assigned to it. `id` is a stable uuid4 (not derived from `name`)
    so renaming a category doesn't invalidate every repo's own
    category_id pointing at it. A repo with no category_id (or one
    pointing at a category that's since been deleted) is simply
    unassigned — nothing currently groups the repo list by this field."""

    id: str
    name: str

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        return cls(id=data["id"], name=data["name"])

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
    the repo's own declared CustomPath catalog (see that class). Surfaced
    to the user via custom_paths_settings_page.py's "Connect Input Path"
    section and, as icons, project_editor_page.py's
    listWidget_repositories_requirements (see get_required_repos below) —
    used to also render as directed edges in the since-removed node graph.
    Named "inputs" (matching the settings page's own "Connect Pipeline
    Input Path..." wording) even though a connection can represent either
    direction of real data flow
    — see RepoRef's docstring and this plugin's README for why the
    separate "outputs" concept was removed 2026-07-19.

    Also wraps the Project-scoped Category catalog (added 2026-08-19,
    project_config_store — see get_categories) and each repo's own
    category_id (get_repo_category_id) that ProjectGraphView's node grid
    groups on instead of the old pipeline-derived automatic layout."""

    def __init__(self, metadata_store: MetadataStore, project_config_store: ProjectPluginConfigStore | None = None):
        self._metadata_store = metadata_store
        # None when no project is active yet (api.project_plugin_config_store's
        # own documented contract) — every category method below no-ops/
        # returns empty rather than assuming this is always real, though in
        # practice this plugin only ever constructs PipelineStore once a
        # project is already guaranteed active (see project_editor.md).
        self._project_config_store = project_config_store

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

    def get_categories(self) -> list[Category]:
        """Every Category declared for the whole active Project — stored
        in Project.plugin_data["project_editor"]["categories"]
        (api.project_plugin_config_store, riding on that project's own
        already-cloud-synced blob, not a separate file). Empty when no
        project config store exists (see __init__)."""
        if self._project_config_store is None:
            return []
        data = self._project_config_store.get(_CATEGORIES_KEY)
        return [Category.from_dict(d) for d in (data or [])]

    def add_category(self, name: str) -> Category:
        """Appends a brand-new Category and persists it immediately —
        used by AssignCategoryDialog's "New Category..." option, which
        needs the real generated id back right away to assign it to the
        repo that triggered the dialog in the same action."""
        category = Category(id=Category.new_id(), name=name)
        categories = self.get_categories()
        categories.append(category)
        self.set_categories(categories)
        return category

    def set_categories(self, categories: list[Category]) -> None:
        """Persists the full Category list, in the given order — the order
        used to be load-bearing for the since-removed node graph's
        top-to-bottom category-box stack (its own right-click "Move
        Category Up"/"Move Category Down"); nothing reads the order for
        display purposes anymore, but it still round-trips unchanged, same
        as add_category's append-and-save."""
        if self._project_config_store is not None:
            self._project_config_store.set(_CATEGORIES_KEY, [c.to_dict() for c in categories])

    def reload_categories(self) -> None:
        """Re-pulls the project config store's own on-disk file after a
        ConflictError from add_category (project_editor_page.py's
        _on_assign_category_clicked) — the rejected push already re-pulled
        the latest data into the local file, but a store held for the whole
        session keeps a stale in-memory copy until this runs, same caveat
        as any other long-lived cloud-synced store."""
        if self._project_config_store is not None:
            self._project_config_store.load()

    def get_repo_category_id(self, project_id: str, repo_id: str) -> str | None:
        """Which Category (by id) this repo is assigned to, or None if
        unassigned. Currently unused by project_editor_page.py — the
        "Assign Categories" button/action was cut from the list UI
        2026-08-19 (same day it was added) per the user's own request; kept
        here since real repos may already have a category_id saved."""
        entry = self._metadata_store.get_repo_plugin_data(project_id, repo_id, PLUGIN_ID)
        return entry.get("category_id")

    def set_repo_category_id(self, project_id: str, repo_id: str, category_id: str | None) -> None:
        self._set_field(project_id, repo_id, "category_id", category_id)

    def get_repo_info(self, project_id: str, repo_id: str) -> str:
        """This repo's free-form info note — textBrowser_info/
        pushButton_edit_info in ProjectEditorTabWindows.ui
        (project_editor_page.py's EditInfoDialog usage). Plain text, empty
        string if never set."""
        entry = self._metadata_store.get_repo_plugin_data(project_id, repo_id, PLUGIN_ID)
        return entry.get("info", "")

    def set_repo_info(self, project_id: str, repo_id: str, text: str) -> None:
        self._set_field(project_id, repo_id, "info", text)

    def _set_field(self, project_id: str, repo_id: str, field_name: str, value) -> None:
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
