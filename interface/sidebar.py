from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.store import MetadataStore
from interface.section_keys import SectionKey
from interface.sidebar_thumbnail import ThumbnailBackgroundWidget

SECTION_LABELS = {
    SectionKey.PROJECT_INFO: "Project Information",
    SectionKey.REPO_BROWSER: "Repo Browser",
    SectionKey.REPO_GIT_STATUS: "Repo Git Status",
    SectionKey.REPO_ABOUT: "Repo About",
}


class Sidebar(QWidget):
    repo_picker_requested = Signal()
    section_changed = Signal(SectionKey)
    combo_repo_selected = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarContainer")
        self.setFixedWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.thumbnail_widget = ThumbnailBackgroundWidget()
        self.thumbnail_widget.setFixedHeight(200)
        thumb_layout = QVBoxLayout(self.thumbnail_widget)
        thumb_layout.addStretch()
        self.repo_name_label = QLabel("—")
        self.repo_name_label.setObjectName("activeRepoLabel")
        thumb_layout.addWidget(self.repo_name_label)

        self.select_repo_button = QPushButton("Select Repo...")
        self.select_repo_button.clicked.connect(self.repo_picker_requested.emit)
        self.repo_combo = QComboBox()
        self.repo_combo.setVisible(False)
        self.repo_combo.currentIndexChanged.connect(self._on_combo_index_changed)

        select_row = QHBoxLayout()
        select_row.addWidget(self.repo_combo, stretch=1)
        select_row.addWidget(self.select_repo_button)
        thumb_layout.addLayout(select_row)

        layout.addWidget(self.thumbnail_widget)

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
        # project_name is intentionally unused now — only the repo name is
        # shown here (project context still visible via the dropdown below).
        self.repo_name_label.setText(repo_name or "—")

    def set_thumbnail(self, path: Path | None) -> None:
        self.thumbnail_widget.set_image(path)

    def set_current_section(self, section: SectionKey) -> None:
        self._section_buttons[section].setChecked(True)

    def refresh_repo_choices(self, store: MetadataStore) -> None:
        cloned = [
            (project, repo)
            for project in store.list_projects()
            for repo in project.repos
            if repo.status == "cloned"
        ]
        if not cloned:
            self.repo_combo.setVisible(False)
            self.select_repo_button.setText("Select Repo...")
            self.select_repo_button.setMaximumWidth(16777215)
            return
        self.repo_combo.blockSignals(True)
        self.repo_combo.clear()
        for project, repo in cloned:
            self.repo_combo.addItem(f"{project.name} / {repo.name}", (project.id, repo.id))
        self.repo_combo.blockSignals(False)
        self.repo_combo.setVisible(True)
        self.select_repo_button.setText("...")
        self.select_repo_button.setMaximumWidth(36)

    def _on_combo_index_changed(self, index: int) -> None:
        if index < 0:
            return
        project_id, repo_id = self.repo_combo.itemData(index)
        self.combo_repo_selected.emit(project_id, repo_id)
