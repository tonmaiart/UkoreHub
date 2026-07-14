from core.store import LocalConfigStore
from core.theme import DEFAULT_THEME_NAME


def test_defaults_when_no_file(tmp_path):
    store = LocalConfigStore(tmp_path / "local_config.json")
    assert store.workspace_root is None
    assert store.theme == DEFAULT_THEME_NAME
    assert store.active_project_id is None
    assert store.active_repo_id is None
    assert store.github_username is None


def test_set_and_persist(tmp_path):
    json_path = tmp_path / "local_config.json"
    store_a = LocalConfigStore(json_path)
    store_a.set_workspace_root("/tmp/workspace")
    store_a.set_theme("grey_dark")
    store_a.set_active_repo("proj-1", "repo-1")
    store_a.set_github_username("octocat")

    store_b = LocalConfigStore(json_path)
    assert store_b.workspace_root == "/tmp/workspace"
    assert store_b.theme == "grey_dark"
    assert store_b.active_project_id == "proj-1"
    assert store_b.active_repo_id == "repo-1"
    assert store_b.github_username == "octocat"


def test_clear_active_repo(tmp_path):
    store = LocalConfigStore(tmp_path / "local_config.json")
    store.set_active_repo("proj-1", "repo-1")
    store.clear_active_repo()
    assert store.active_project_id is None
    assert store.active_repo_id is None


def test_backward_compat_missing_keys(tmp_path):
    json_path = tmp_path / "local_config.json"
    json_path.write_text('{"workspace_root": "/tmp/old"}', encoding="utf-8")
    store = LocalConfigStore(json_path)
    assert store.workspace_root == "/tmp/old"
    assert store.theme == DEFAULT_THEME_NAME
    assert store.active_project_id is None
