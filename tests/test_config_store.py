from core.store import LocalConfigStore
from core.theme import DEFAULT_THEME_NAME


def test_defaults_when_no_file(tmp_path):
    store = LocalConfigStore(tmp_path / "local_config.json")
    assert store.workspace_root is None
    assert store.theme == DEFAULT_THEME_NAME
    assert store.active_project_id is None
    assert store.active_repo_id is None
    assert store.github_username is None
    assert store.recent_files == {}


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
    assert store.recent_files == {}


def test_get_recent_files_empty_when_unset(tmp_path):
    store = LocalConfigStore(tmp_path / "local_config.json")
    assert store.get_recent_files("repo-1") == []


def test_add_recent_file_inserts_at_front(tmp_path):
    store = LocalConfigStore(tmp_path / "local_config.json")
    store.add_recent_file("repo-1", "/repo/a.ma")
    updated = store.add_recent_file("repo-1", "/repo/b.ma")
    assert updated == ["/repo/b.ma", "/repo/a.ma"]


def test_add_recent_file_dedup_moves_to_front(tmp_path):
    store = LocalConfigStore(tmp_path / "local_config.json")
    store.add_recent_file("repo-1", "/repo/a.ma")
    store.add_recent_file("repo-1", "/repo/b.ma")
    updated = store.add_recent_file("repo-1", "/repo/a.ma")
    assert updated == ["/repo/a.ma", "/repo/b.ma"]


def test_add_recent_file_respects_limit(tmp_path):
    store = LocalConfigStore(tmp_path / "local_config.json")
    for i in range(5):
        store.add_recent_file("repo-1", f"/repo/{i}.ma", limit=3)
    assert store.get_recent_files("repo-1") == ["/repo/4.ma", "/repo/3.ma", "/repo/2.ma"]


def test_recent_files_scoped_per_repo(tmp_path):
    store = LocalConfigStore(tmp_path / "local_config.json")
    store.add_recent_file("repo-1", "/repo1/a.ma")
    store.add_recent_file("repo-2", "/repo2/b.ma")
    assert store.get_recent_files("repo-1") == ["/repo1/a.ma"]
    assert store.get_recent_files("repo-2") == ["/repo2/b.ma"]


def test_recent_files_persist_and_reload(tmp_path):
    json_path = tmp_path / "local_config.json"
    LocalConfigStore(json_path).add_recent_file("repo-1", "/repo/a.ma")
    reloaded = LocalConfigStore(json_path)
    assert reloaded.get_recent_files("repo-1") == ["/repo/a.ma"]
