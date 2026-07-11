from core.store import SystemConfigStore


def test_defaults_when_no_file(tmp_path):
    store = SystemConfigStore(tmp_path / "system_config.json")
    assert store.github_client_id is None


def test_set_and_persist(tmp_path):
    json_path = tmp_path / "system_config.json"
    store_a = SystemConfigStore(json_path)
    store_a.set_github_client_id("abc123")

    store_b = SystemConfigStore(json_path)
    assert store_b.github_client_id == "abc123"


def test_set_empty_string_clears_to_none(tmp_path):
    json_path = tmp_path / "system_config.json"
    store = SystemConfigStore(json_path)
    store.set_github_client_id("abc123")
    store.set_github_client_id("")
    assert store.github_client_id is None
