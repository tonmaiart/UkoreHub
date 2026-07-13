from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget

from interface.section_registry import SectionRegistry


class TopTabBar(QWidget):
    """Row of repo-scoped tab buttons embedded in MenuBar — one button per
    registered SectionRegistry section (built-in and plugin-provided alike,
    in registry order): Repo, Explorer, Submit, About. Setting is
    deliberately NOT part of this bar (and not in this exclusive button
    group) — it's an app-level control, not a repo-scoped one, and lives as
    its own button in MenuBar after the GitHub login/logout widget."""

    tab_changed = Signal(str)

    def __init__(self, parent=None, *, section_registry: SectionRegistry):
        super().__init__(parent)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._buttons: dict[str, QPushButton] = {}
        for index, spec in enumerate(section_registry.ordered()):
            button = QPushButton(spec.label)
            button.setObjectName("topTabButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked, key=spec.key: self.tab_changed.emit(key))
            self.button_group.addButton(button)
            self._buttons[spec.key] = button
            layout.addWidget(button)
            if index == 0:
                button.setChecked(True)

    def uncheck_all(self) -> None:
        # Called by MainWindow when the separate Setting button (not part of
        # this bar's exclusive group) is clicked, so only one control across
        # the whole window ever looks active at a time. Qt's exclusive
        # QButtonGroup silently refuses to uncheck the sole checked button
        # via setChecked(False) — toggling exclusivity off/on is the
        # documented way around that.
        self.button_group.setExclusive(False)
        for button in self._buttons.values():
            button.setChecked(False)
        self.button_group.setExclusive(True)
