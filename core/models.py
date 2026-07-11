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
    required_program_ids: list[str] = field(default_factory=list)

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
            required_program_ids=data.get("required_program_ids", []),
        )


@dataclass
class Program:
    id: str
    name: str
    icon_filename: str | None = None
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Program":
        return cls(
            id=data["id"],
            name=data["name"],
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
