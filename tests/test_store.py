import json
from pathlib import Path

import pytest

from core.exceptions import ValidationError
from core.store import MetadataStore


@pytest.fixture
def store(tmp_path):
    return MetadataStore(tmp_path / "projects.json")


def test_add_project_creates_entry(store):
    project = store.add_project("Kafka")
    assert project.name == "Kafka"
    assert store.list_projects() == [project]


def test_duplicate_project_name_raises_validation_error(store):
    store.add_project("Kafka")
    with pytest.raises(ValidationError):
        store.add_project("kafka")


def test_add_repo_computes_local_path(store, tmp_path):
    project = store.add_project("Kafka")
    workspace_root = str(tmp_path / "workspace")
    repo = store.add_repo(project.id, "repo1", "git@example.com:org/repo1.git", workspace_root)
    assert repo.local_path == str(Path("Kafka") / "repo1")
    assert repo.status == "not_cloned"
    assert repo.last_synced is None


def test_edit_repo_updates_fields(store, tmp_path):
    project = store.add_project("Kafka")
    workspace_root = str(tmp_path / "workspace")
    repo = store.add_repo(project.id, "repo1", "git@example.com:org/repo1.git", workspace_root)
    store.edit_repo(project.id, repo.id, name="repo1-renamed", git_url="git@example.com:org/other.git")
    updated = store.get_repo(project.id, repo.id)
    assert updated.name == "repo1-renamed"
    assert updated.git_url == "git@example.com:org/other.git"


def test_delete_project_removes_repo_children(store, tmp_path):
    project = store.add_project("Kafka")
    workspace_root = str(tmp_path / "workspace")
    store.add_repo(project.id, "repo1", "git@example.com:org/repo1.git", workspace_root)
    store.delete_project(project.id)
    assert store.list_projects() == []


def test_store_persists_and_reloads(tmp_path):
    json_path = tmp_path / "projects.json"
    store_a = MetadataStore(json_path)
    project = store_a.add_project("Kafka")
    store_a.add_repo(project.id, "repo1", "git@example.com:org/repo1.git", str(tmp_path / "workspace"))

    store_b = MetadataStore(json_path)
    projects = store_b.list_projects()
    assert len(projects) == 1
    assert projects[0].name == "Kafka"
    assert len(projects[0].repos) == 1
    assert projects[0].repos[0].name == "repo1"


def test_new_repo_has_empty_enabled_addon_ids(store, tmp_path):
    project = store.add_project("Kafka")
    workspace_root = str(tmp_path / "workspace")
    repo = store.add_repo(project.id, "repo1", "git@example.com:org/repo1.git", workspace_root)
    assert repo.enabled_addon_ids == []


def test_set_repo_enabled_addons(store, tmp_path):
    project = store.add_project("Kafka")
    workspace_root = str(tmp_path / "workspace")
    repo = store.add_repo(project.id, "repo1", "git@example.com:org/repo1.git", workspace_root)
    store.set_repo_enabled_addons(project.id, repo.id, ["maya_launcher", "asset_tracker"])
    updated = store.get_repo(project.id, repo.id)
    assert updated.enabled_addon_ids == ["maya_launcher", "asset_tracker"]


def _projects_json_with_repo(extra_repo_fields: dict) -> dict:
    return {
        "schema_version": 1,
        "projects": [
            {
                "id": "p1",
                "name": "Kafka",
                "repos": [
                    {
                        "id": "r1",
                        "name": "repo1",
                        "git_url": "git@example.com:org/repo1.git",
                        "local_path": "Kafka/repo1",
                        **extra_repo_fields,
                    }
                ],
            }
        ],
    }


def test_repo_enabled_addon_ids_backward_compat_missing_key(tmp_path):
    json_path = tmp_path / "projects.json"
    json_path.write_text(json.dumps(_projects_json_with_repo({})), encoding="utf-8")
    store = MetadataStore(json_path)
    assert store.get_repo("p1", "r1").enabled_addon_ids == []


def test_repo_enabled_addon_ids_backward_compat_legacy_key(tmp_path):
    json_path = tmp_path / "projects.json"
    json_path.write_text(
        json.dumps(_projects_json_with_repo({"enabled_plugin_ids": ["maya_launcher"]})), encoding="utf-8"
    )
    store = MetadataStore(json_path)
    assert store.get_repo("p1", "r1").enabled_addon_ids == ["maya_launcher"]
