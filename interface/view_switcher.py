from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget

REPO = "repo"
SETTING = "setting"


class ViewSwitcher(QWidget):
    """Bottom bar toggling MainWindow's two top-level views — same
    exclusive-checkable-button pattern as Sidebar's section buttons."""

    view_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        self.repo_button = QPushButton("Repo")
        self.repo_button.setCheckable(True)
        self.repo_button.setChecked(True)
        self.repo_button.clicked.connect(lambda: self.view_changed.emit(REPO))

        self.setting_button = QPushButton("Setting")
        self.setting_button.setCheckable(True)
        self.setting_button.clicked.connect(lambda: self.view_changed.emit(SETTING))

        self.button_group.addButton(self.repo_button)
        self.button_group.addButton(self.setting_button)

        layout = QHBoxLayout(self)
        layout.addWidget(self.repo_button)
        layout.addWidget(self.setting_button)
        layout.addStretch()
