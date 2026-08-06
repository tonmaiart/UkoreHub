from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from core.program_store import ProgramStore

_NODE_KIND_ROLE = Qt.UserRole + 1


class RequirementsTreeWidget(QTreeWidget):
    """Each Program is a checkable top-level node (check = required), with
    a checkable child per version for a multi-version Program (pin, radio-
    style). Used by RepoDialog (repo creation) and
    interface/repo_settings/requirements_and_plugins_page.py (editing an
    existing repo's requirements)."""

    def __init__(
        self,
        parent=None,
        *,
        program_store: ProgramStore,
        selected_program_ids: list[str] | None = None,
        selected_program_version_pins: dict[str, str] | None = None,
    ):
        super().__init__(parent)
        self.setHeaderHidden(True)

        selected_program_id_set = set(selected_program_ids or [])
        version_pins = selected_program_version_pins or {}

        for program in program_store.list_programs():
            version_suffix = f" (v{', '.join(program.versions)})" if program.versions else ""
            program_item = QTreeWidgetItem([f"{program.name}{version_suffix}"])
            program_item.setFlags(program_item.flags() | Qt.ItemIsUserCheckable)
            program_item.setCheckState(0, Qt.Checked if program.id in selected_program_id_set else Qt.Unchecked)
            program_item.setData(0, Qt.UserRole, program.id)
            program_item.setData(0, _NODE_KIND_ROLE, "program")
            icon_path = program_store.resolve_icon_path(program)
            if icon_path and icon_path.exists():
                program_item.setIcon(0, QIcon(str(icon_path)))
            if len(program.versions) > 1:
                pinned = version_pins.get(program.id)
                default_version = pinned if pinned in program.versions else program.versions[0]
                for version in program.versions:
                    version_item = QTreeWidgetItem([version])
                    version_item.setFlags(version_item.flags() | Qt.ItemIsUserCheckable)
                    version_item.setCheckState(0, Qt.Checked if version == default_version else Qt.Unchecked)
                    version_item.setData(0, Qt.UserRole, version)
                    version_item.setData(0, _NODE_KIND_ROLE, "version")
                    program_item.addChild(version_item)
            self.addTopLevelItem(program_item)
            program_item.setExpanded(True)

        self.itemChanged.connect(self._on_tree_item_changed)

    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        kind = item.data(0, _NODE_KIND_ROLE)
        if kind == "version" and item.checkState(0) == Qt.Checked:
            # Version children under one Program are exclusive (radio-style)
            # — picking one is the repo's pin, so uncheck any other version
            # sibling.
            parent = item.parent()
            if parent is None:
                return
            for i in range(parent.childCount()):
                sibling = parent.child(i)
                if (
                    sibling is not item
                    and sibling.data(0, _NODE_KIND_ROLE) == "version"
                    and sibling.checkState(0) == Qt.Checked
                ):
                    sibling.setCheckState(0, Qt.Unchecked)

    def selected_program_ids(self) -> list[str]:
        selected = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, _NODE_KIND_ROLE) == "program" and item.checkState(0) == Qt.Checked:
                selected.append(item.data(0, Qt.UserRole))
        return selected

    def selected_program_version_pins(self) -> dict[str, str]:
        pins: dict[str, str] = {}
        for i in range(self.topLevelItemCount()):
            program_item = self.topLevelItem(i)
            if program_item.data(0, _NODE_KIND_ROLE) != "program":
                continue
            program_id = program_item.data(0, Qt.UserRole)
            for j in range(program_item.childCount()):
                child = program_item.child(j)
                if child.data(0, _NODE_KIND_ROLE) == "version" and child.checkState(0) == Qt.Checked:
                    pins[program_id] = child.data(0, Qt.UserRole)
                    break
        return pins
