from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Callable

from core.exceptions import NotFoundError, ValidationError
from core.models import Program, Project, Repo
from core.storage.atomic_file import atomic_write, utc_now_iso
from core.vcs.git_service import GitService
from core.vcs.paths import resolve_repo_path

SCHEMA_VERSION = 2


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
    """Project/Repo registry. On disk (and as GCS blobs, see core/vcs/cloud_sync.py)
    this is split into a lightweight index (json_path itself, id/name only)
    plus one file per project under projects_dir — editing one project's repos
    only ever rewrites/pushes that project's own blob, never the whole
    registry. See developer/app/docs/data-layout.md for the exact layout."""

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
        # Unlike SystemConfigStore's on_save (no-arg — one fixed blob), this
        # store's on_save takes the blob name that just changed
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
            # layout immediately (mirrors the git->cloud-sync cutover, see
            # the ukorehub-cloud-sync skill) so this only ever runs once
            # per machine/bucket.
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
        atomic_write(self.json_path, data)
        if self.on_save:
            self.on_save("projects.json")

    def _save_project(self, project: Project) -> None:
        atomic_write(self.projects_dir / f"{project.id}.json", project.to_dict())
        if self.on_save:
            self.on_save(f"projects/{project.id}.json")

    def list_projects(self) -> list[Project]:
        return list(self.projects)

    def get_project(self, project_id: str) -> Project:
            for i, project in enumerate(self.projects):
                if project.id == project_id:
                    # 🟢 Clean Fix: ถ้า repos เป็น list ว่าง ให้โหลดจาก project blob ย่อยทันที
                    if not project.repos:
                        project_blob_path = self.projects_dir / f"{project_id}.json"
                        if project_blob_path.exists():
                            project_data = json.loads(project_blob_path.read_text(encoding="utf-8"))
                            loaded_project = Project.from_dict(project_data)
                            self.projects[i] = loaded_project
                            return loaded_project
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
        local_path = resolve_repo_path(workspace_root, project.name, git_url)
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
        repo.last_synced = utc_now_iso()
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

    def get_repo_plugin_data(self, project_id: str, repo_id: str, plugin_id: str) -> dict:
        return self.get_repo(project_id, repo_id).plugin_data.get(plugin_id, {})

    def set_repo_plugin_data(self, project_id: str, repo_id: str, plugin_id: str, data: dict) -> None:
        project = self.get_project(project_id)
        repo = self.get_repo(project_id, repo_id)
        repo.plugin_data[plugin_id] = data
        self._save_project(project)

    def get_project_plugin_data(self, project_id: str, plugin_id: str) -> dict:
        return self.get_project(project_id).plugin_data.get(plugin_id, {})

    def set_project_plugin_data(self, project_id: str, plugin_id: str, data: dict) -> None:
        project = self.get_project(project_id)
        project.plugin_data[plugin_id] = data
        self._save_project(project)

    @property
    def thumbnails_dir(self) -> Path:
        return self.assets_dir / "thumbnails"

    def resolve_thumbnail_path(self, repo: Repo) -> Path | None:
        if not repo.thumbnail_filename:
            return None
        return self.thumbnails_dir / repo.thumbnail_filename

    def refresh_statuses_from_disk(self, project_id: str, workspace_root: str, git_service: GitService) -> None:
        """Reconciles Repo.status against what's actually on disk, for the
        case where an artist manually copies an already-cloned repo folder
        into workspace_root instead of letting Sync clone it (e.g. to skip a
        slow first clone). Called by launcher.py once per app launch,
        scoped to just the active project rather than every project in the
        store — this runs a git subprocess per repo, so scanning every
        project studio-wide on every launch isn't free.

        Uses git_service.is_repo_root(), not the cheaper is_cloned(),
        because a folder that didn't come from this app's own clone() call
        is exactly the case the ukorehub-core skill warns about: a
        broken/partial .git directory doesn't stop git's repo-discovery
        walk, so a plain ".git" existence check can silently resolve to
        some unrelated repo further up the tree instead of failing."""
        project = self.get_project(project_id)
        changed = False
        for repo in project.repos:
            abs_path = Path(workspace_root) / repo.local_path
            new_status = "cloned" if git_service.is_repo_root(abs_path) else "not_cloned"
            if new_status != repo.status:
                repo.status = new_status
                changed = True
        if changed:
            self._save_project(project)

    def list_programs(self, project_id: str) -> list[Program]:
        return list(self.get_project(project_id).programs)

    def get_program(self, project_id: str, program_id: str) -> Program:
        for program in self.get_project(project_id).programs:
            if program.id == program_id:
                return program
        raise NotFoundError(f"Program not found: {program_id}")

    def add_program(
        self, project_id: str, name: str, description: str = "", versions: list[str] | None = None
    ) -> Program:
        project = self.get_project(project_id)
        name = name.strip()
        if not name:
            raise ValidationError("Program name cannot be empty.")
        if any(p.name.lower() == name.lower() for p in project.programs):
            raise ValidationError(f"A program named '{name}' already exists.")
        program = Program(
            id=str(uuid.uuid4()), name=name, versions=list(versions or []), description=description.strip()
        )
        project.programs.append(program)
        self._save_project(project)
        return program

    def edit_program(
        self,
        project_id: str,
        program_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        versions: list[str] | None = None,
    ) -> None:
        project = self.get_project(project_id)
        program = self.get_program(project_id, program_id)
        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError("Program name cannot be empty.")
            if any(p.id != program_id and p.name.lower() == name.lower() for p in project.programs):
                raise ValidationError(f"A program named '{name}' already exists.")
            program.name = name
        if description is not None:
            program.description = description.strip()
        if versions is not None:
            program.versions = list(versions)
        self._save_project(project)

    def delete_program(self, project_id: str, program_id: str) -> None:
        project = self.get_project(project_id)
        program = self.get_program(project_id, program_id)
        project.programs.remove(program)
        self._save_project(project)

    def set_program_icon(self, project_id: str, program_id: str, filename: str | None) -> None:
        project = self.get_project(project_id)
        program = self.get_program(project_id, program_id)
        program.icon_filename = filename
        self._save_project(project)

    @property
    def program_icons_dir(self) -> Path:
        return self.assets_dir / "program_icons"

    def resolve_program_icon_path(self, program: Program) -> Path | None:
        if not program.icon_filename:
            return None
        return self.program_icons_dir / program.icon_filename


def migrate_legacy_programs(store: MetadataStore, legacy_path: Path) -> None:
    """One-time cutover from the old studio-wide data/programs.json catalog
    into each Project's own Project.programs — Program Database used to be
    one list shared by the whole studio, now each Project has its own. Only
    migrates Programs a repo somewhere actually requires (so existing
    required_program_ids/program_version_pins keep resolving); a Program
    nobody requires has no signal for which Project it belongs to, so it's
    deliberately left behind in the old file rather than guessed at —
    still readable via Settings > Developer > Cloud Data if a studio admin
    needs to recreate it by hand. Idempotent via a presence check (copies
    only if not already there) rather than clearing legacy_path, since that
    file is being kept in place on purpose. Safe to call on every launch."""
    legacy_path = Path(legacy_path)
    if not legacy_path.exists():
        return
    data = json.loads(legacy_path.read_text(encoding="utf-8"))
    legacy_programs = {p["id"]: p for p in data.get("programs", [])}
    if not legacy_programs:
        return
    for project in store.projects:
        existing_ids = {p.id for p in project.programs}
        changed = False
        for repo in project.repos:
            for program_id in list(repo.required_program_ids) + list(repo.program_version_pins.keys()):
                if program_id in existing_ids or program_id not in legacy_programs:
                    continue
                project.programs.append(Program.from_dict(legacy_programs[program_id]))
                existing_ids.add(program_id)
                changed = True
        if changed:
            store._save_project(project)
