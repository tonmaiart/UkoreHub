from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

from interface.section_keys import SectionKey

SECTION_LABELS = {
    SectionKey.PROJECT_INFO: "Project Information",
    SectionKey.REPO_BROWSER: "Repo Browser",
    SectionKey.REPO_GIT_STATUS: "Repo Git Status",
    SectionKey.REPO_ABOUT: "Repo About",
}


class Sidebar(QWidget):
    repo_picker_requested = Signal()
    section_changed = Signal(SectionKey)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo_placeholder = QFrame()
        logo_placeholder.setObjectName("sidebarLogoPlaceholder")
        logo_placeholder.setFixedHeight(120)
        layout.addWidget(logo_placeholder)

        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        self.project_label = QLabel("Current Project: —")
        self.repo_label = QLabel("Current Repo: —")
        self.select_repo_button = QPushButton("Select Repo...")
        self.select_repo_button.clicked.connect(self.repo_picker_requested.emit)
        info_layout.addWidget(self.project_label)
        info_layout.addWidget(self.repo_label)
        info_layout.addWidget(self.select_repo_button)
        layout.addWidget(info_container)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self._section_buttons: dict[SectionKey, QPushButton] = {}
        for index, section in enumerate(SectionKey):
            button = QPushButton(SECTION_LABELS[section])
            button.setObjectName("sectionButton")
            button.setCheckable(True)
            button.setFixedHeight(40)
            button.clicked.connect(lambda _checked, s=section: self.section_changed.emit(s))
            self.button_group.addButton(button)
            self._section_buttons[section] = button
            layout.addWidget(button)
            if index == 0:
                button.setChecked(True)

        layout.addStretch()

    def set_active_labels(self, project_name: str | None, repo_name: str | None) -> None:
        self.project_label.setText(f"Current Project: {project_name or '—'}")
        self.repo_label.setText(f"Current Repo: {repo_name or '—'}")

    def set_current_section(self, section: SectionKey) -> None:
        self._section_buttons[section].setChecked(True)
