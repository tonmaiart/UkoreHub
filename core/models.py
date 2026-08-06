from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class BrowserLink:
    """A repo-scoped bookmark (e.g. a Google Sheet, a Canva board) shown as
    its own top-level tab embedding that URL — configured under
    Settings > Repo > Browser, see interface/about/browser_link_page.py."""

    name: str
    url: str
    icon_filename: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BrowserLink":
        return cls(name=data["name"], url=data["url"], icon_filename=data.get("icon_filename"))


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
    # plugins/repo_internal/maya_launcher/link_resolution.py's pinned_version().
    # A Program with 0/1 versions needs no entry here.
    program_version_pins: dict[str, str] = field(default_factory=dict)
    # Formerly an opt-out list over plugins/core entries. No longer read
    # anywhere (2026-08-04 — every plugins/core plugin is unconditionally
    # visible for every repo now, see interface/main_window.py's
    # _apply_plugin_visibility and plugins/README.md); kept as a field
    # purely so existing persisted JSON with this key still round-trips
    # cleanly. See required_plugin_ids below for the opt-in model actually
    # in use, for plugins/repo_internal and cache/plugins.
    active_plugin_ids: list[str] = field(default_factory=list)
    # Which plugins/repo_internal entries this repo has opted into. Unlike
    # active_plugin_ids above, empty here means "none" — a repo_internal
    # plugin is bundled with the app (no separate git fetch, unlike a
    # cache/plugins/ repo plugin) but stays hidden for a repo until that
    # repo explicitly requires it, same opt-in shape as required_program_ids.
    # See interface/main_window.py's _apply_plugin_visibility.
    required_plugin_ids: list[str] = field(default_factory=list)
    browser_links: list[BrowserLink] = field(default_factory=list)

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
            browser_links=[BrowserLink.from_dict(bl) for bl in data.get("browser_links", [])],
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
