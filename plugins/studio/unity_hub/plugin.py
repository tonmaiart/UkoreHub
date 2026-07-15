from __future__ import annotations

import subprocess

from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from interface.section_registry import SectionSpec

PLUGIN_ID = "unity_hub"
PROGRAM_NAME = "Unity Hub"
# Convention-only string match with plugins/studio/software_linker/plugin.py
# — both resolve to the same data/plugins/local/software_linker.json via
# PluginConfigStore, no coupling API needed. Same pattern
# plugins/studio/maya_launcher uses to find a linked maya.exe.
SOFTWARE_LINKER_PLUGIN_ID = "software_linker"


def _find_program(program_store):
    for program in program_store.list_programs():
        if program.name.strip().lower() == PROGRAM_NAME.lower():
            return program
    return None


def _ensure_program(program_store) -> None:
    """Best-effort: makes sure a "Unity Hub" Program Database entry exists,
    so it shows up in Settings > Software Linker for the user to link a
    local Unity Hub.exe path to without any manual Program Database setup
    step first."""
    if _find_program(program_store) is None:
        program_store.add_program(PROGRAM_NAME)


class UnityHubPage(QWidget):
    """Nothing but a button — launches whatever local Unity Hub.exe path
    the user linked via Settings > Software Linker."""

    def __init__(self, parent=None, *, program_store, config_store):
        super().__init__(parent)
        self._program_store = program_store
        self._config_store = config_store

        open_button = QPushButton("Open Unity Hub")
        open_button.clicked.connect(self._on_open)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Unity Hub"))
        layout.addWidget(open_button)
        layout.addStretch()

    def _on_open(self) -> None:
        program = _find_program(self._program_store)
        exe_path = self._config_store.get(program.id) if program is not None else None
        if not exe_path:
            QMessageBox.information(
                self,
                "Unity Hub",
                "No linked Unity Hub executable found. Configure it in Settings > Software Linker.",
            )
            return
        try:
            subprocess.Popen([exe_path])
        except OSError as exc:
            QMessageBox.warning(self, "Unity Hub", f"Could not launch Unity Hub:\n{exc}")


def register(api) -> None:
    _ensure_program(api.programs)
    api.register_section(
        SectionSpec(
            key=PLUGIN_ID,
            label="Unity Hub",
            order=40,
            page_factory=lambda: UnityHubPage(
                program_store=api.programs,
                config_store=api.plugin_config_store(SOFTWARE_LINKER_PLUGIN_ID, shared=False),
            ),
        )
    )
