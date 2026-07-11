from __future__ import annotations

import json
import uuid
from pathlib import Path

from core.exceptions import NotFoundError, ValidationError
from core.models import Program
from core.store import _atomic_write

SCHEMA_VERSION = 1


class ProgramStore:
    """Shared studio-wide catalog of pipeline software (Maya, Nuke, ...) that
    Repos can declare as requirements. Backed by data/programs.json, tracked
    in git alongside projects.json (same "system config" category)."""

    def __init__(self, json_path: Path):
        self.json_path = Path(json_path)
        self.programs: list[Program] = []
        self.load()

    def load(self) -> None:
        if not self.json_path.exists():
            self.programs = []
            self.save()
            return
        data = json.loads(self.json_path.read_text(encoding="utf-8"))
        self.programs = [Program.from_dict(p) for p in data.get("programs", [])]

    def save(self) -> None:
        data = {
            "schema_version": SCHEMA_VERSION,
            "programs": [p.to_dict() for p in self.programs],
        }
        _atomic_write(self.json_path, data)

    def list_programs(self) -> list[Program]:
        return list(self.programs)

    def get_program(self, program_id: str) -> Program:
        for program in self.programs:
            if program.id == program_id:
                return program
        raise NotFoundError(f"Program not found: {program_id}")

    def add_program(self, name: str, description: str = "") -> Program:
        name = name.strip()
        if not name:
            raise ValidationError("Program name cannot be empty.")
        if any(p.name.lower() == name.lower() for p in self.programs):
            raise ValidationError(f"A program named '{name}' already exists.")
        program = Program(id=str(uuid.uuid4()), name=name, description=description.strip())
        self.programs.append(program)
        self.save()
        return program

    def edit_program(self, program_id: str, *, name: str | None = None, description: str | None = None) -> None:
        program = self.get_program(program_id)
        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError("Program name cannot be empty.")
            if any(p.id != program_id and p.name.lower() == name.lower() for p in self.programs):
                raise ValidationError(f"A program named '{name}' already exists.")
            program.name = name
        if description is not None:
            program.description = description.strip()
        self.save()

    def delete_program(self, program_id: str) -> None:
        program = self.get_program(program_id)
        self.programs.remove(program)
        self.save()

    def set_program_icon(self, program_id: str, filename: str | None) -> None:
        program = self.get_program(program_id)
        program.icon_filename = filename
        self.save()

    @property
    def icons_dir(self) -> Path:
        return self.json_path.parent / "program_icons"

    def resolve_icon_path(self, program: Program) -> Path | None:
        if not program.icon_filename:
            return None
        return self.icons_dir / program.icon_filename
