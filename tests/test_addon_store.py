import pytest

from core.addon_store import AddonMetadataStore, group_addon_ids_by_program


@pytest.fixture
def addon_store(tmp_path):
    return AddonMetadataStore(tmp_path / "addon_settings.json")


def test_get_unknown_addon_returns_default(addon_store):
    metadata = addon_store.get("maya_launcher")
    assert metadata.addon_id == "maya_launcher"
    assert metadata.description == ""
    assert metadata.icon_filename is None
    assert metadata.required_program_ids == []


def test_set_description_creates_and_updates_entry(addon_store):
    addon_store.set_description("maya_launcher", "  Bridges Maya env vars  ")
    assert addon_store.get("maya_launcher").description == "Bridges Maya env vars"


def test_set_icon(addon_store):
    addon_store.set_icon("maya_launcher", "abc123.png")
    metadata = addon_store.get("maya_launcher")
    assert metadata.icon_filename == "abc123.png"
    assert addon_store.resolve_icon_path(metadata) == addon_store.icons_dir / "abc123.png"


def test_resolve_icon_path_none_when_unset(addon_store):
    metadata = addon_store.get("maya_launcher")
    assert addon_store.resolve_icon_path(metadata) is None


def test_set_required_program_ids(addon_store):
    addon_store.set_required_program_ids("advanced_skeleton", ["maya-program-id"])
    assert addon_store.get("advanced_skeleton").required_program_ids == ["maya-program-id"]


def test_store_persists_and_reloads(tmp_path):
    json_path = tmp_path / "addon_settings.json"
    store_a = AddonMetadataStore(json_path)
    store_a.set_description("maya_launcher", "Bridge")
    store_a.set_icon("maya_launcher", "icon.png")
    store_a.set_required_program_ids("maya_launcher", ["p1"])

    store_b = AddonMetadataStore(json_path)
    metadata = store_b.get("maya_launcher")
    assert metadata.description == "Bridge"
    assert metadata.icon_filename == "icon.png"
    assert metadata.required_program_ids == ["p1"]


def test_group_addon_ids_by_program(addon_store):
    addon_store.set_required_program_ids("maya_launcher", ["maya"])
    addon_store.set_required_program_ids("advanced_skeleton", ["maya"])
    addon_store.set_required_program_ids("cross_dcc_tool", ["maya", "unity"])
    # "unlabeled_addon" left with no required programs

    by_program, ungrouped = group_addon_ids_by_program(
        ["maya_launcher", "advanced_skeleton", "cross_dcc_tool", "unlabeled_addon"], addon_store
    )

    assert set(by_program["maya"]) == {"maya_launcher", "advanced_skeleton", "cross_dcc_tool"}
    assert by_program["unity"] == ["cross_dcc_tool"]
    assert ungrouped == ["unlabeled_addon"]
