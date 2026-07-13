from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from core.exceptions import NotFoundError, ValidationError
from core.models import Project, Repo
from core.paths import resolve_repo_path
from core.theme import DEFAULT_THEME_NAME

SCHEMA_VERSION = 1


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp_path, path)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MetadataStore:
    def __init__(self, json_path: Path):
        self.json_path = Path(json_path)
        self.projects: list[Project] = []
        self.load()

    def load(self) -> None:
        if not self.json_path.exists():
            self.projects = []
            self.save()
            return
        data = json.loads(self.json_path.read_text(encoding="utf-8"))
        self.projects = [Project.from_dict(p) for p in data.get("projects", [])]

    def save(self) -> None:
        data = {
            "schema_version": SCHEMA_VERSION,
            "projects": [p.to_dict() for p in self.projects],
        }
        _atomic_write(self.json_path, data)

    def list_projects(self) -> list[Project]:
        return list(self.projects)

    def get_project(self, project_id: str) -> Project:
        for project in self.projects:
            if project.id == project_id:
                return project
        raise NotFoundError(f"Project not found: {project_id}")

    def get_repo(self, project_id: str, repo_id: str) -> Repo:
        project = self.get_project(project_id)
        for repo in project.repos:
            if repo.id == repo_id:
                return repo
        raise NotFoundError(f"Repo not found: {repo_id}")

    def add_project(self, name: str) -> Project:
        name = name.strip()
        if not name:
            raise ValidationError("Project name cannot be empty.")
        if any(p.name.lower() == name.lower() for p in self.projects):
            raise ValidationError(f"A project named '{name}' already exists.")
        project = Project(id=str(uuid.uuid4()), name=name, repos=[])
        self.projects.append(project)
        self.save()
        return project

    def rename_project(self, project_id: str, new_name: str) -> None:
        new_name = new_name.strip()
        if not new_name:
            raise ValidationError("Project name cannot be empty.")
        project = self.get_project(project_id)
        if any(p.id != project_id and p.name.lower() == new_name.lower() for p in self.projects):
            raise ValidationError(f"A project named '{new_name}' already exists.")
        project.name = new_name
        self.save()

    def delete_project(self, project_id: str) -> None:
        project = self.get_project(project_id)
        self.projects.remove(project)
        self.save()

    def add_repo(self, project_id: str, name: str, git_url: str, workspace_root: str) -> Repo:
        name = name.strip()
        git_url = git_url.strip()
        if not name:
            raise ValidationError("Repo name cannot be empty.")
        if not git_url:
            raise ValidationError("Repo git URL cannot be empty.")
        project = self.get_project(project_id)
        if any(r.name.lower() == name.lower() for r in project.repos):
            raise ValidationError(f"A repo named '{name}' already exists in '{project.name}'.")
        local_path = resolve_repo_path(workspace_root, project.name, name)
        try:
            relative_local_path = local_path.relative_to(workspace_root)
        except ValueError:
            relative_local_path = local_path
        repo = Repo(
            id=str(uuid.uuid4()),
            name=name,
            git_url=git_url,
            local_path=str(relative_local_path),
            last_synced=None,
            status="not_cloned",
        )
        project.repos.append(repo)
        self.save()
        return repo

    def edit_repo(self, project_id: str, repo_id: str, *, name: str | None = None, git_url: str | None = None) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError("Repo name cannot be empty.")
            if any(r.id != repo_id and r.name.lower() == name.lower() for r in project.repos):
                raise ValidationError(f"A repo named '{name}' already exists in '{project.name}'.")
            repo.name = name
        if git_url is not None:
            git_url = git_url.strip()
            if not git_url:
                raise ValidationError("Repo git URL cannot be empty.")
            repo.git_url = git_url
        self.save()

    def delete_repo(self, project_id: str, repo_id: str) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        project.repos.remove(repo)
        self.save()

    def mark_synced(self, project_id: str, repo_id: str, status: str) -> None:
        repo = self.get_repo(project_id, repo_id)
        repo.status = status
        repo.last_synced = _utc_now_iso()
        self.save()

    def mark_status(self, project_id: str, repo_id: str, status: str) -> None:
        repo = self.get_repo(project_id, repo_id)
        repo.status = status
        self.save()

    def set_repo_thumbnail(self, project_id: str, repo_id: str, filename: str | None) -> None:
        repo = self.get_repo(project_id, repo_id)
        repo.thumbnail_filename = filename
        self.save()

    def set_repo_requirements(self, project_id: str, repo_id: str, program_ids: list[str]) -> None:
        repo = self.get_repo(project_id, repo_id)
        repo.required_program_ids = list(program_ids)
        self.save()

    def set_repo_enabled_addons(self, project_id: str, repo_id: str, addon_ids: list[str]) -> None:
        repo = self.get_repo(project_id, repo_id)
        repo.enabled_addon_ids = list(addon_ids)
        self.save()

    @property
    def thumbnails_dir(self) -> Path:
        return self.json_path.parent / "thumbnails"

    def resolve_thumbnail_path(self, repo: Repo) -> Path | None:
        if not repo.thumbnail_filename:
            return None
        return self.thumbnails_dir / repo.thumbnail_filename

    def refresh_statuses_from_disk(self, workspace_root: str) -> None:
        for project in self.projects:
            for repo in project.repos:
                abs_path = Path(workspace_root) / repo.local_path
                is_cloned = (abs_path / ".git").exists()
                repo.status = "cloned" if is_cloned else "not_cloned"
        self.save()


LOCAL_CONFIG_SCHEMA_VERSION = 1
SYSTEM_CONFIG_SCHEMA_VERSION = 1


class LocalConfigStore:
    """Per-machine settings — never shared, gitignored.

    Each artist's own workspace folder, theme preference, and "what am I
    currently working on" state live here, separate from the team-shared
    SystemConfigStore and the shared MetadataStore registry.
    """

    def __init__(self, json_path: Path):
        self.json_path = Path(json_path)
        self.workspace_root: str | None = None
        self.theme: str = DEFAULT_THEME_NAME
        self.active_project_id: str | None = None
        self.active_repo_id: str | None = None
        self.github_username: str | None = None
        self.recent_files: dict[str, list[str]] = {}
        self.load()

    def load(self) -> None:
        if not self.json_path.exists():
            return
        data = json.loads(self.json_path.read_text(encoding="utf-8"))
        self.workspace_root = data.get("workspace_root")
        self.theme = data.get("theme", DEFAULT_THEME_NAME)
        self.active_project_id = data.get("active_project_id")
        self.active_repo_id = data.get("active_repo_id")
        self.github_username = data.get("github_username")
        self.recent_files = data.get("recent_files", {})

    def save(self) -> None:
        _atomic_write(
            self.json_path,
            {
                "schema_version": LOCAL_CONFIG_SCHEMA_VERSION,
                "workspace_root": self.workspace_root,
                "theme": self.theme,
                "active_project_id": self.active_project_id,
                "active_repo_id": self.active_repo_id,
                "github_username": self.github_username,
                "recent_files": self.recent_files,
            },
        )

    def add_recent_file(self, repo_id: str, path: str, limit: int = 10) -> list[str]:
        paths = [p for p in self.recent_files.get(repo_id, []) if p != path]
        paths.insert(0, path)
        paths = paths[:limit]
        self.recent_files[repo_id] = paths
        self.save()
        return list(paths)

    def get_recent_files(self, repo_id: str) -> list[str]:
        return list(self.recent_files.get(repo_id, []))

    def set_workspace_root(self, path: str) -> None:
        self.workspace_root = path
        self.save()

    def set_theme(self, name: str) -> None:
        self.theme = name
        self.save()

    def set_active_repo(self, project_id: str, repo_id: str) -> None:
        self.active_project_id = project_id
        self.active_repo_id = repo_id
        self.save()

    def clear_active_repo(self) -> None:
        self.active_project_id = None
        self.active_repo_id = None
        self.save()

    def set_github_username(self, username: str | None) -> None:
        self.github_username = username
        self.save()


class SystemConfigStore:
    """Studio-wide settings meant to be committed to the UkoreHub repo itself
    and shared to everyone via git (e.g. through the self-update pull), the
    same way the MetadataStore registry (data/projects.json) is shared.
    """

    def __init__(self, json_path: Path):
        self.json_path = Path(json_path)
        self.github_client_id: str | None = None
        self.load()

    def load(self) -> None:
        if not self.json_path.exists():
            return
        data = json.loads(self.json_path.read_text(encoding="utf-8"))
        self.github_client_id = data.get("github_client_id")

    def save(self) -> None:
        _atomic_write(
            self.json_path,
            {
                "schema_version": SYSTEM_CONFIG_SCHEMA_VERSION,
                "github_client_id": self.github_client_id,
            },
        )

    def set_github_client_id(self, client_id: str) -> None:
        self.github_client_id = client_id or None
        self.save()
