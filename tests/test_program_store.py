import pytest

from core.exceptions import ValidationError
from core.program_store import ProgramStore


@pytest.fixture
def program_store(tmp_path):
    return ProgramStore(tmp_path / "programs.json")


def test_add_program_creates_entry(program_store):
    program = program_store.add_program("Maya", "3D animation software")
    assert program.name == "Maya"
    assert program.description == "3D animation software"
    assert program_store.list_programs() == [program]


def test_duplicate_program_name_raises_validation_error(program_store):
    program_store.add_program("Maya")
    with pytest.raises(ValidationError):
        program_store.add_program("maya")


def test_edit_program_updates_fields(program_store):
    program = program_store.add_program("Maya")
    program_store.edit_program(program.id, name="Autodesk Maya", description="Updated")
    updated = program_store.get_program(program.id)
    assert updated.name == "Autodesk Maya"
    assert updated.description == "Updated"


def test_delete_program(program_store):
    program = program_store.add_program("Maya")
    program_store.delete_program(program.id)
    assert program_store.list_programs() == []


def test_set_program_icon_and_resolve_path(program_store):
    program = program_store.add_program("Maya")
    program_store.set_program_icon(program.id, "abc123.png")
    reloaded = program_store.get_program(program.id)
    assert program_store.resolve_icon_path(reloaded) == program_store.icons_dir / "abc123.png"


def test_resolve_icon_path_none_when_unset(program_store):
    program = program_store.add_program("Maya")
    assert program_store.resolve_icon_path(program) is None


def test_store_persists_and_reloads(tmp_path):
    json_path = tmp_path / "programs.json"
    store_a = ProgramStore(json_path)
    store_a.add_program("Maya", "3D software")

    store_b = ProgramStore(json_path)
    programs = store_b.list_programs()
    assert len(programs) == 1
    assert programs[0].name == "Maya"
    assert programs[0].description == "3D software"
