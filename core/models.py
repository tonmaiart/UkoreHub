from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class Repo:
    id: str
    name: str
    git_url: str
    local_path: str
    last_synced: str | None = None
    status: str = "not_cloned"
    thumbnail_filename: str | None = None
    description: str = ""
    required_program_ids: list[str] = field(default_factory=list)
    # Which specific version this repo launches for a multi-version Program
    # in required_program_ids (e.g. {"<maya_program_id>": "2024"}) — see
    # maya_launcher's link_resolution.py's pinned_version() (now its own
    # cache/plugins/ clone, see developer/app/docs/plugins-guide.md).
    # A Program with 0/1 versions needs no entry here.
    program_version_pins: dict[str, str] = field(default_factory=dict)
    # Formerly an opt-out list over plugins/core entries. No longer read
    # anywhere (2026-08-04 — every plugins/core plugin is unconditionally
    # visible for every repo now, see interface/main_window.py's
    # _apply_plugin_visibility and developer/app/docs/plugins-guide.md); kept as a field
    # purely so existing persisted JSON with this key still round-trips
    # cleanly. See required_plugin_ids below for the opt-in model actually
    # in use, for cache/plugins entries.
    active_plugin_ids: list[str] = field(default_factory=list)
    # Which cache/plugins/ entries (each its own separate git clone) this
    # repo has opted into. Empty here means "none" — a cache/plugins/ entry
    # stays hidden for a repo until that repo explicitly requires it, same
    # opt-in shape as required_program_ids. See interface/main_window.py's
    # _apply_plugin_visibility.
    required_plugin_ids: list[str] = field(default_factory=list)
    # Free-form per-plugin data genuinely scoped to this one repo, keyed by
    # plugin_id — e.g. project_editor's pipeline_inputs/custom_paths,
    # maya_publisher's publish_mode. core/ never interprets the value, same
    # "core doesn't know plugin shapes" contract PluginConfigStore has (see
    # core/extensibility/config_store.py) — this just travels with the repo
    # instead of living in its own separate data/plugins/core/<id>.json
    # blob, so a repo-level edit only ever pushes/conflicts this repo's own
    # project blob. Only for data that's actually (project_id, repo_id)-scoped
    # — studio-wide or cross-project plugin data still belongs in
    # PluginConfigStore(shared=True), see developer/app/docs/plugins-guide.md.
    plugin_data: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Repo":
        return cls(
            id=data["id"],
            name=data["name"],
            git_url=data["git_url"],
            local_path=data["local_path"],
            last_synced=data.get("last_synced"),
            status=data.get("status", "not_cloned"),
            thumbnail_filename=data.get("thumbnail_filename"),
            description=data.get("description", ""),
            required_program_ids=data.get("required_program_ids", []),
            program_version_pins=data.get("program_version_pins", {}),
            active_plugin_ids=data.get("active_plugin_ids", []),
            required_plugin_ids=data.get("required_plugin_ids", []),
            plugin_data=data.get("plugin_data", {}),
        )


@dataclass
class Program:
    id: str
    name: str
    versions: list[str] = field(default_factory=list)
    icon_filename: str | None = None
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Program":
        # versions replaces the older single-string version key — fall back
        # to it so catalog entries saved before this rename still load.
        versions = data.get("versions") or ([data["version"]] if data.get("version") else [])
        return cls(
            id=data["id"],
            name=data["name"],
            versions=versions,
            icon_filename=data.get("icon_filename"),
            description=data.get("description", ""),
        )


@dataclass
class CommitInfo:
    hash: str
    author: str
    email: str
    date: str
    message: str


@dataclass
class FileChange:
    path: str
    change_type: str  # "untracked" | "added" | "modified" | "deleted" | "renamed"


@dataclass
class RepoStatus:
    commit: CommitInfo | None
    unstaged_changes: list[FileChange]
    staged_changes: list[FileChange]
    is_clean: bool


@dataclass
class Project:
    id: str
    name: str
    repos: list[Repo] = field(default_factory=list)
    # This Project's own Program Database (pipeline software catalog, e.g.
    # "Autodesk Maya") — not shared with other Projects. A Repo's
    # required_program_ids/program_version_pins only ever resolve against
    # its owning Project's own programs list. See core/store.py's
    # MetadataStore.list_programs/get_program/etc.
    programs: list[Program] = field(default_factory=list)
    # Free-form per-plugin data genuinely scoped to this Project as a whole
    # (not a specific Repo — see Repo.plugin_data above for that), keyed by
    # plugin_id. Rides inside this Project's own blob, so it's already
    # cloud-synced via MetadataStore's existing per-project push/pull — no
    # separate data/plugins/core/<id>.json blob needed. Meant for data
    # that's inherently session/project-scoped rather than studio-wide (e.g.
    # maya_launcher's MAYA_ENV_BRIDGE contributions, see
    # core/extensibility/config_store.py's ProjectPluginConfigStore) —
    # genuinely studio-wide data still belongs in PluginConfigStore(shared=True).
    plugin_data: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "repos": [repo.to_dict() for repo in self.repos],
            "programs": [program.to_dict() for program in self.programs],
            "plugin_data": self.plugin_data,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(
            id=data["id"],
            name=data["name"],
            repos=[Repo.from_dict(r) for r in data.get("repos", [])],
            programs=[Program.from_dict(p) for p in data.get("programs", [])],
            plugin_data=data.get("plugin_data", {}),
        )
