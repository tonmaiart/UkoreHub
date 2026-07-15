from __future__ import annotations

from dataclasses import dataclass

from core.extensibility.config_store import PluginConfigStore

# Top-level key inside pipeline_architect's PluginConfigStore JSON file
# (data/plugins/studio/pipeline_architect.json) holding the whole nested
# project_id -> repo_id -> {pipeline_inputs, pipeline_outputs} tree — see
# README.md for the exact shape and how another plugin should read it.
_PROJECTS_KEY = "projects"


@dataclass
class RepoRef:
    """A (project_id, repo_id) pair — every cross-repo reference in this
    codebase is stored as a pair rather than a bare repo id (ExplorerPin,
    local_config_store.active_project_id/active_repo_id, RepoPickerDialog's
    own return shape), since MetadataStore.get_repo(project_id, repo_id)
    always needs both regardless of whether Repo.id UUIDs happen to be
    globally unique."""

    project_id: str
    repo_id: str

    def to_dict(self) -> dict:
        return {"project_id": self.project_id, "repo_id": self.repo_id}

    @classmethod
    def from_dict(cls, data: dict) -> "RepoRef":
        return cls(project_id=data["project_id"], repo_id=data["repo_id"])


class PipelineStore:
    """Wraps pipeline_architect's PluginConfigStore "projects" key — one
    repo's declared pipeline inputs (repos that feed into it) and outputs
    (repos it feeds into), curated independently of each other (no
    auto-mirroring: listing B as an input of A does not automatically add A
    as an output of B)."""

    def __init__(self, config_store: PluginConfigStore):
        self._config_store = config_store

    def _tree(self) -> dict:
        return self._config_store.get(_PROJECTS_KEY, {})

    @staticmethod
    def _repo_entry(tree: dict, project_id: str, repo_id: str) -> dict:
        return tree.get(project_id, {}).get("repos", {}).get(repo_id, {})

    def get_inputs(self, project_id: str, repo_id: str) -> list[RepoRef]:
        entry = self._repo_entry(self._tree(), project_id, repo_id)
        return [RepoRef.from_dict(d) for d in entry.get("pipeline_inputs", [])]

    def get_outputs(self, project_id: str, repo_id: str) -> list[RepoRef]:
        entry = self._repo_entry(self._tree(), project_id, repo_id)
        return [RepoRef.from_dict(d) for d in entry.get("pipeline_outputs", [])]

    def set_inputs(self, project_id: str, repo_id: str, refs: list[RepoRef]) -> None:
        self._set_field(project_id, repo_id, "pipeline_inputs", refs)

    def set_outputs(self, project_id: str, repo_id: str, refs: list[RepoRef]) -> None:
        self._set_field(project_id, repo_id, "pipeline_outputs", refs)

    def _set_field(self, project_id: str, repo_id: str, field_name: str, refs: list[RepoRef]) -> None:
        tree = self._tree()
        repos = tree.setdefault(project_id, {}).setdefault("repos", {})
        repo_entry = repos.setdefault(repo_id, {})
        repo_entry[field_name] = [ref.to_dict() for ref in refs]
        self._config_store.set(_PROJECTS_KEY, tree)
