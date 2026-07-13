import json

from core.extensibility.config_store import PluginConfigStore


def test_get_default_when_missing(tmp_path):
    store = PluginConfigStore(tmp_path / "plugin.json")
    assert store.get("missing_key") is None
    assert store.get("missing_key", "fallback") == "fallback"


def test_set_then_get_round_trips(tmp_path):
    store = PluginConfigStore(tmp_path / "plugin.json")
    store.set("maya_executable_path", "C:/maya.exe")
    assert store.get("maya_executable_path") == "C:/maya.exe"


def test_set_persists_to_disk_immediately(tmp_path):
    json_path = tmp_path / "plugin.json"
    store = PluginConfigStore(json_path)
    store.set("key", "value")
    assert json.loads(json_path.read_text(encoding="utf-8")) == {"key": "value"}


def test_reloading_store_sees_previously_set_values(tmp_path):
    json_path = tmp_path / "plugin.json"
    PluginConfigStore(json_path).set("key", 42)
    reloaded = PluginConfigStore(json_path)
    assert reloaded.get("key") == 42
