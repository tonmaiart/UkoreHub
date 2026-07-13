from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.store import MetadataStore
from interface.circular_pixmap import circular_pixmap
from interface.sidebar_thumbnail import ThumbnailBackgroundWidget

AVATAR_BADGE_SIZE = 56


class Sidebar(QWidget):
    repo_picker_requested = Signal()
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

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(AVATAR_BADGE_SIZE, AVATAR_BADGE_SIZE)
        self.repo_name_label = QLabel("—")
        self.repo_name_label.setObjectName("activeRepoLabel")
        name_row = QHBoxLayout()
        name_row.addWidget(self.avatar_label)
        name_row.addWidget(self.repo_name_label, stretch=1)
        thumb_layout.addLayout(name_row)

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

        layout.addStretch()

    def set_active_labels(self, project_name: str | None, repo_name: str | None) -> None:
        # project_name is intentionally unused now — only the repo name is
        # shown here (project context still visible via the dropdown below).
        self.repo_name_label.setText(repo_name or "—")

    def set_thumbnail(self, path: Path | None) -> None:
        self.thumbnail_widget.set_image(path)
        pixmap = QPixmap(str(path)) if path and Path(path).exists() else None
        if pixmap is not None and not pixmap.isNull():
            self.avatar_label.setPixmap(circular_pixmap(pixmap, AVATAR_BADGE_SIZE))
        else:
            self.avatar_label.clear()

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
