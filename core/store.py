from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from core.exceptions import NotFoundError, ValidationError
from core.models import BrowserLink, Project, Repo
from core.paths import resolve_repo_path
from core.theme import DEFAULT_THEME_NAME

SCHEMA_VERSION = 2


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp_path, path)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_project_ids(json_path: Path) -> list[str] | None:
    """Reads just the project ids out of a projects.json index file, without
    constructing a full MetadataStore — used by launcher.py to know which
    per-project blobs to pull from GCS before MetadataStore.load() runs.
    Returns None if json_path doesn't exist yet, or is still the old
    pre-split shape (schema_version < 2, repos embedded) — callers should
    skip per-project pulls in that case and let MetadataStore.load()'s
    one-time migration handle it locally."""
    json_path = Path(json_path)
    if not json_path.exists():
        return None
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if data.get("schema_version", 1) < 2:
        return None
    return [entry["id"] for entry in data.get("projects", [])]


class MetadataStore:
    """Project/Repo registry. On disk (and as GCS blobs, see core/cloud_sync.py)
    this is split into a lightweight index (json_path itself, id/name only)
    plus one file per project under projects_dir — editing one project's repos
    only ever rewrites/pushes that project's own blob, never the whole
    registry. See data/README.md for the exact layout."""

    def __init__(
        self,
        json_path: Path,
        *,
        assets_dir: Path | None = None,
        on_save: Callable[[str], None] | None = None,
        on_delete: Callable[[str], None] | None = None,
    ):
        self.json_path = Path(json_path)
        # Binary images (thumbnails, browser link icon overrides) are
        # git-tracked assets, not cloud-synced data — they live in their own
        # assets/ tree, not alongside json_path. Defaults to json_path's
        # grandparent / "assets" (<repo_root>/assets) for callers that don't
        # care about resolving image paths and never pass this explicitly.
        self.assets_dir = Path(assets_dir) if assets_dir is not None else self.json_path.parent.parent / "assets"
        # Per-project blobs live in a sibling "projects" folder next to the
        # index, e.g. data/projects.json (index) + data/projects/<id>.json.
        self.projects_dir = self.json_path.parent / "projects"
        self.projects: list[Project] = []
        # Unlike SystemConfigStore/ProgramStore's on_save (no-arg — one fixed
        # blob), this store's on_save takes the blob name that just changed
        # ("projects.json" for the index, "projects/<id>.json" for a single
        # project) so a repo-level edit only ever pushes that one project's
        # blob, not the whole registry.
        self.on_save = on_save
        # Only used by delete_project — pushes a blob's deletion to the
        # shared bucket so removing a project doesn't leave a permanent
        # orphan behind.
        self.on_delete = on_delete
        self.load()

    def load(self) -> None:
        if not self.json_path.exists():
            self.projects = []
            self._save_index()
            return
        data = json.loads(self.json_path.read_text(encoding="utf-8"))
        if data.get("schema_version", 1) < 2:
            # Old shape: every project's "repos" were embedded directly in
            # the index file. Split them out once and persist the new
            # layout immediately (mirrors the git->GCS cutover in
            # developer/bug-history/2026-08-09-shared-data-git-pull-conflict.md)
            # so this only ever runs once per machine/bucket.
            self.projects = [Project.from_dict(p) for p in data.get("projects", [])]
            for project in self.projects:
                self._save_project(project)
            self._save_index()
            return
        self.projects = []
        for entry in data.get("projects", []):
            project_path = self.projects_dir / f"{entry['id']}.json"
            if project_path.exists():
                project_data = json.loads(project_path.read_text(encoding="utf-8"))
                self.projects.append(Project.from_dict(project_data))
            else:
                # Index references a project whose own blob hasn't synced to
                # this machine (or was lost) — surface it as an empty-repos
                # project rather than dropping it from the list entirely.
                self.projects.append(Project(id=entry["id"], name=entry["name"], repos=[]))

    def _save_index(self) -> None:
        data = {
            "schema_version": SCHEMA_VERSION,
            "projects": [{"id": p.id, "name": p.name} for p in self.projects],
        }
        _atomic_write(self.json_path, data)
        if self.on_save:
            self.on_save("projects.json")

    def _save_project(self, project: Project) -> None:
        _atomic_write(self.projects_dir / f"{project.id}.json", project.to_dict())
        if self.on_save:
            self.on_save(f"projects/{project.id}.json")

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
        # Write the project's own blob before the index so a crash between
        # the two never leaves the index pointing at a file that doesn't
        # exist yet.
        self._save_project(project)
        self._save_index()
        return project

    def rename_project(self, project_id: str, new_name: str) -> None:
        new_name = new_name.strip()
        if not new_name:
            raise ValidationError("Project name cannot be empty.")
        project = self.get_project(project_id)
        if any(p.id != project_id and p.name.lower() == new_name.lower() for p in self.projects):
            raise ValidationError(f"A project named '{new_name}' already exists.")
        project.name = new_name
        # Name is duplicated in both the index and the project's own blob.
        self._save_project(project)
        self._save_index()

    def delete_project(self, project_id: str) -> None:
        project = self.get_project(project_id)
        self.projects.remove(project)
        # Index is the source of truth for "what projects exist" — update it
        # first, then clean up the now-orphaned per-project blob.
        self._save_index()
        (self.projects_dir / f"{project.id}.json").unlink(missing_ok=True)
        if self.on_delete:
            self.on_delete(f"projects/{project.id}.json")

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
        self._save_project(project)
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
        self._save_project(project)

    def delete_repo(self, project_id: str, repo_id: str) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        project.repos.remove(repo)
        self._save_project(project)

    def mark_synced(self, project_id: str, repo_id: str, status: str) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        repo.status = status
        repo.last_synced = _utc_now_iso()
        self._save_project(project)

    def mark_status(self, project_id: str, repo_id: str, status: str) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        repo.status = status
        self._save_project(project)

    def set_repo_thumbnail(self, project_id: str, repo_id: str, filename: str | None) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        repo.thumbnail_filename = filename
        self._save_project(project)

    def set_repo_description(self, project_id: str, repo_id: str, description: str) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        repo.description = description
        self._save_project(project)

    def set_repo_requirements(self, project_id: str, repo_id: str, program_ids: list[str]) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        repo.required_program_ids = list(program_ids)
        self._save_project(project)

    def set_repo_program_version_pins(self, project_id: str, repo_id: str, pins: dict[str, str]) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        repo.program_version_pins = dict(pins)
        self._save_project(project)

    def set_repo_active_plugin_ids(self, project_id: str, repo_id: str, plugin_ids: list[str]) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        repo.active_plugin_ids = list(plugin_ids)
        self._save_project(project)

    def set_repo_required_plugin_ids(self, project_id: str, repo_id: str, plugin_ids: list[str]) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        repo.required_plugin_ids = list(plugin_ids)
        self._save_project(project)

    def set_repo_browser_links(self, project_id: str, repo_id: str, links: list[BrowserLink]) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        repo.browser_links = list(links)
        self._save_project(project)

    def set_browser_link_icon(self, project_id: str, repo_id: str, link_index: int, filename: str | None) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        if not (0 <= link_index < len(repo.browser_links)):
            raise NotFoundError(f"Browser link index out of range: {link_index}")
        repo.browser_links[link_index].icon_filename = filename
        self._save_project(project)

    @property
    def thumbnails_dir(self) -> Path:
        return self.assets_dir / "thumbnails"

    def resolve_thumbnail_path(self, repo: Repo) -> Path | None:
        if not repo.thumbnail_filename:
            return None
        return self.thumbnails_dir / repo.thumbnail_filename

    @property
    def browser_link_icons_dir(self) -> Path:
        return self.assets_dir / "browser_link_icons"

    def resolve_browser_link_icon_path(self, link: BrowserLink) -> Path | None:
        if not link.icon_filename:
            return None
        return self.browser_link_icons_dir / link.icon_filename

    def refresh_statuses_from_disk(self, workspace_root: str) -> None:
        for project in self.projects:
            changed = False
            for repo in project.repos:
                abs_path = Path(workspace_root) / repo.local_path
                is_cloned = (abs_path / ".git").exists()
                new_status = "cloned" if is_cloned else "not_cloned"
                if new_status != repo.status:
                    repo.status = new_status
                    changed = True
            if changed:
                self._save_project(project)


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
        self.github_login_at: str | None = None
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
        self.github_login_at = data.get("github_login_at")

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
                "github_login_at": self.github_login_at,
            },
        )

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

    def set_github_login_at(self, timestamp: str | None) -> None:
        self.github_login_at = timestamp
        self.save()


class SystemConfigStore:
    """Studio-wide settings shared to everyone via Google Cloud Storage (see
    core/cloud_sync.py), the same way the MetadataStore registry
    (data/projects.json) is shared. `on_save`, when provided by the caller,
    pushes the freshly-saved file up to the shared bucket.
    """

    def __init__(self, json_path: Path, *, on_save: Callable[[], None] | None = None):
        self.json_path = Path(json_path)
        self.github_client_id: str | None = None
        self.gcs_bucket_name: str | None = None
        self.gcs_project_id: str | None = None
        self.google_oauth_client_id: str | None = None
        self.google_oauth_client_secret: str | None = None
        self.on_save = on_save
        self.load()

    def load(self) -> None:
        if not self.json_path.exists():
            return
        data = json.loads(self.json_path.read_text(encoding="utf-8"))
        self.github_client_id = data.get("github_client_id")
        self.gcs_bucket_name = data.get("gcs_bucket_name")
        self.gcs_project_id = data.get("gcs_project_id")
        self.google_oauth_client_id = data.get("google_oauth_client_id")
        self.google_oauth_client_secret = data.get("google_oauth_client_secret")

    def save(self) -> None:
        _atomic_write(
            self.json_path,
            {
                "schema_version": SYSTEM_CONFIG_SCHEMA_VERSION,
                "github_client_id": self.github_client_id,
                "gcs_bucket_name": self.gcs_bucket_name,
                "gcs_project_id": self.gcs_project_id,
                "google_oauth_client_id": self.google_oauth_client_id,
                "google_oauth_client_secret": self.google_oauth_client_secret,
            },
        )
        if self.on_save:
            self.on_save()

    def set_github_client_id(self, client_id: str) -> None:
        self.github_client_id = client_id or None
        self.save()

    def set_gcs_bucket_name(self, bucket_name: str) -> None:
        self.gcs_bucket_name = bucket_name or None
        self.save()

    def set_gcs_project_id(self, project_id: str) -> None:
        self.gcs_project_id = project_id or None
        self.save()

    def set_google_oauth_client_id(self, client_id: str) -> None:
        self.google_oauth_client_id = client_id or None
        self.save()

    def set_google_oauth_client_secret(self, client_secret: str) -> None:
        self.google_oauth_client_secret = client_secret or None
        self.save()
