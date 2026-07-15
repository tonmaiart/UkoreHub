from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class BrowserLink:
    """A repo-scoped bookmark (e.g. a Google Sheet, a Canva board) shown as
    its own top-level tab embedding that URL — see Repo About's Browser
    Links section and interface/about/browser_link_page.py."""

    name: str
    url: str
    icon_filename: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BrowserLink":
        return cls(name=data["name"], url=data["url"], icon_filename=data.get("icon_filename"))


@dataclass
class ExplorerPin:
    """A repo-scoped pin onto another repo's file browser — its own extra
    Explorer-style sidebar tab while this repo is active (see
    plugins/studio/explorer/pinned_repo_browser_page.py), independent of
    the app's global active repo. Both target ids are stored (not just
    target_repo_id) so lookup goes through MetadataStore.get_repo(project_id,
    repo_id) the same way every other repo reference in this codebase does
    (local_config_store.active_project_id/active_repo_id,
    RepoPickerDialog.selected_project_id()/selected_repo_id())."""

    target_project_id: str
    target_repo_id: str
    label: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ExplorerPin":
        return cls(
            target_project_id=data["target_project_id"],
            target_repo_id=data["target_repo_id"],
            label=data["label"],
        )


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
    enabled_addon_ids: list[str] = field(default_factory=list)
    # Which plugins/studio + plugins/local entries actually apply to this
    # repo — a distinct, brand-new key (not enabled_plugin_ids, which is
    # already claimed as enabled_addon_ids' own legacy fallback key below).
    # Empty means "unrestricted" (every discovered plugin stays active),
    # so existing/unconfigured repos never silently lose functionality.
    active_plugin_ids: list[str] = field(default_factory=list)
    browser_links: list[BrowserLink] = field(default_factory=list)
    # Other repos pinned as extra Explorer-style sidebar tabs while this
    # repo is active — see ExplorerPin above and
    # plugins/studio/explorer/explorer_settings_page.py.
    explorer_pins: list[ExplorerPin] = field(default_factory=list)

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
            # enabled_addon_ids replaces the older enabled_plugin_ids key —
            # fall back to it so repos saved before this rename still load.
            enabled_addon_ids=data.get("enabled_addon_ids", data.get("enabled_plugin_ids", [])),
            active_plugin_ids=data.get("active_plugin_ids", []),
            browser_links=[BrowserLink.from_dict(bl) for bl in data.get("browser_links", [])],
            explorer_pins=[ExplorerPin.from_dict(ep) for ep in data.get("explorer_pins", [])],
        )


@dataclass
class Program:
    id: str
    name: str
    version: str = ""
    icon_filename: str | None = None
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Program":
        return cls(
            id=data["id"],
            name=data["name"],
            version=data.get("version", ""),
            icon_filename=data.get("icon_filename"),
            description=data.get("description", ""),
        )


@dataclass
class AddonMetadata:
    """Studio-editable overrides layered on top of an add-on's own
    manifest.json — icon, description override, and which Program(s) it
    extends. Keyed by the manifest's own id, not owned by the add-on's
    folder since add-on/ content is vendored code, not a JSON store."""

    addon_id: str
    icon_filename: str | None = None
    description: str = ""
    required_program_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AddonMetadata":
        return cls(
            addon_id=data["addon_id"],
            icon_filename=data.get("icon_filename"),
            description=data.get("description", ""),
            required_program_ids=data.get("required_program_ids", []),
        )


@dataclass
class CommitInfo:
    hash: str
    author: str
    email: str
    date: str
    message: str


@dataclass
class RepoStatus:
    commit: CommitInfo | None
    untracked: list[str]
    modified: list[str]
    staged: list[str]
    is_clean: bool


@dataclass
class Project:
    id: str
    name: str
    repos: list[Repo] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "repos": [repo.to_dict() for repo in self.repos],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(
            id=data["id"],
            name=data["name"],
            repos=[Repo.from_dict(r) for r in data.get("repos", [])],
        )
