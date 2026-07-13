import json

from core.extensibility.loader import PluginLoadFailure, apply_plugins, discover_plugins, plugin_source

API_VERSION = 1


def _write_manifest(plugin_dir, *, id, api_version=API_VERSION, entry_point="plugin.py", version="0.1.0"):
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "id": id,
                "name": id,
                "version": version,
                "api_version": api_version,
                "entry_point": entry_point,
            }
        ),
        encoding="utf-8",
    )


def _write_entry_point(plugin_dir, *, filename="plugin.py", body="def register(api):\n    pass\n"):
    (plugin_dir / filename).write_text(body, encoding="utf-8")


def test_discover_valid_plugin(tmp_path):
    root = tmp_path / "studio"
    plugin_dir = root / "hello"
    _write_manifest(plugin_dir, id="hello")
    _write_entry_point(plugin_dir)

    result = discover_plugins([root], api_version=API_VERSION)

    assert len(result.loaded) == 1
    assert result.failures == []
    assert result.loaded[0].manifest.id == "hello"
    assert hasattr(result.loaded[0].module, "register")


def test_missing_manifest_is_a_failure_not_a_crash(tmp_path):
    root = tmp_path / "studio"
    plugin_dir = root / "broken"
    plugin_dir.mkdir(parents=True)

    result = discover_plugins([root], api_version=API_VERSION)

    assert result.loaded == []
    assert len(result.failures) == 1
    assert "no manifest.json" in result.failures[0].reason


def test_malformed_manifest_is_a_failure(tmp_path):
    root = tmp_path / "studio"
    plugin_dir = root / "broken"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text("{not valid json", encoding="utf-8")

    result = discover_plugins([root], api_version=API_VERSION)

    assert result.loaded == []
    assert len(result.failures) == 1


def test_api_version_mismatch_is_skipped(tmp_path):
    root = tmp_path / "studio"
    plugin_dir = root / "old"
    _write_manifest(plugin_dir, id="old", api_version=999)
    _write_entry_point(plugin_dir)

    result = discover_plugins([root], api_version=API_VERSION)

    assert result.loaded == []
    assert len(result.failures) == 1
    assert "api_version" in result.failures[0].reason


def test_missing_entry_point_is_a_failure(tmp_path):
    root = tmp_path / "studio"
    plugin_dir = root / "no_entry"
    _write_manifest(plugin_dir, id="no_entry")
    # entry_point file intentionally not written

    result = discover_plugins([root], api_version=API_VERSION)

    assert result.loaded == []
    assert len(result.failures) == 1


def test_broken_entry_point_import_is_isolated(tmp_path):
    root = tmp_path / "studio"
    plugin_dir = root / "raises_on_import"
    _write_manifest(plugin_dir, id="raises_on_import")
    _write_entry_point(plugin_dir, body="raise RuntimeError('boom')\n")

    result = discover_plugins([root], api_version=API_VERSION)

    assert result.loaded == []
    assert len(result.failures) == 1
    assert "boom" in result.failures[0].reason


def test_duplicate_id_across_roots_first_root_wins(tmp_path):
    studio_root = tmp_path / "studio"
    local_root = tmp_path / "local"
    _write_manifest(studio_root / "dup", id="dup")
    _write_entry_point(studio_root / "dup")
    _write_manifest(local_root / "dup", id="dup")
    _write_entry_point(local_root / "dup")

    result = discover_plugins([studio_root, local_root], api_version=API_VERSION)

    assert len(result.loaded) == 1
    assert result.loaded[0].dir_path == studio_root / "dup"
    assert len(result.failures) == 1
    assert "duplicate" in result.failures[0].reason


def test_nonexistent_root_is_skipped_silently(tmp_path):
    result = discover_plugins([tmp_path / "does_not_exist"], api_version=API_VERSION)
    assert result.loaded == []
    assert result.failures == []


class _FakeApi:
    def __init__(self):
        self.calls = []


def test_apply_plugins_calls_register_on_each(tmp_path):
    root = tmp_path / "studio"
    _write_manifest(root / "hello", id="hello")
    _write_entry_point(root / "hello", body="def register(api):\n    api.calls.append('hello')\n")

    result = discover_plugins([root], api_version=API_VERSION)
    api = _FakeApi()
    failures = apply_plugins(result.loaded, api)

    assert failures == []
    assert api.calls == ["hello"]


def test_apply_plugins_isolates_a_broken_register(tmp_path):
    root = tmp_path / "studio"
    _write_manifest(root / "a", id="a")
    _write_entry_point(root / "a", body="def register(api):\n    raise RuntimeError('register boom')\n")
    _write_manifest(root / "b", id="b")
    _write_entry_point(root / "b", body="def register(api):\n    api.calls.append('b')\n")

    result = discover_plugins([root], api_version=API_VERSION)
    api = _FakeApi()
    failures = apply_plugins(result.loaded, api)

    assert api.calls == ["b"]
    assert len(failures) == 1
    assert isinstance(failures[0], PluginLoadFailure)
    assert "register boom" in failures[0].reason


def test_apply_plugins_reports_missing_register_function(tmp_path):
    root = tmp_path / "studio"
    _write_manifest(root / "no_register", id="no_register")
    _write_entry_point(root / "no_register", body="X = 1\n")

    result = discover_plugins([root], api_version=API_VERSION)
    failures = apply_plugins(result.loaded, _FakeApi())

    assert len(failures) == 1
    assert "register" in failures[0].reason


def test_plugin_source_studio_root(tmp_path):
    root = tmp_path / "studio"
    _write_manifest(root / "hello", id="hello")
    _write_entry_point(root / "hello")

    result = discover_plugins([root], api_version=API_VERSION)

    assert plugin_source(result.loaded[0]) == "studio"


def test_plugin_source_local_root(tmp_path):
    root = tmp_path / "local"
    _write_manifest(root / "hello", id="hello")
    _write_entry_point(root / "hello")

    result = discover_plugins([root], api_version=API_VERSION)

    assert plugin_source(result.loaded[0]) == "local"
