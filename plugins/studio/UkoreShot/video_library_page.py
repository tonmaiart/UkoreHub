from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from interface.shared.widget_helpers import show_exclusive
from plugins.studio.UkoreShot import video_path_store
from plugins.studio.UkoreShot.player_widget import PlayerWidget
from plugins.studio.UkoreShot.thumbnail_loader import ThumbnailLoader

_VIDEO_EXTENSIONS = {".mov", ".mp4", ".avi"}
_ICON_SIZE = QSize(120, 68)


class UkoreShotPage(QWidget):
    """The UkoreShot sidebar tab's page — a thumbnail-grid video library
    browser (left) plus PlayerWidget (right, playback + grease-pencil
    drawing/comments) for whichever video is selected. Implements the
    standard set_repo() page protocol (interface/main_window.py's
    _apply_to_current_page/_set_active_repo) so it re-resolves its video
    root whenever the active repo changes or this tab regains focus."""

    def __init__(self, parent=None, *, api):
        super().__init__(parent)
        self._api = api
        self._project_id: str | None = None
        self._repo_id: str | None = None
        self._video_root: Path | None = None
        self._thumbnail_loader = ThumbnailLoader(self)
        self._thumbnail_loader.thumbnailReady.connect(self._on_thumbnail_ready)

        self.empty_label = QLabel("Select a repo to see this information.")
        self.empty_label.setWordWrap(True)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(_ICON_SIZE)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setMovement(QListWidget.Static)
        self.list_widget.setSpacing(8)
        self.list_widget.setWrapping(False)
        self.list_widget.setFlow(QListWidget.TopToBottom)
        self.list_widget.currentItemChanged.connect(self._on_current_item_changed)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._reload_videos)
        self.list_empty_label = QLabel("No videos found yet.")
        self.list_empty_label.setWordWrap(True)
        self.list_empty_label.setProperty("secondary", True)

        left_panel = QWidget()
        left_panel.setMaximumWidth(280)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.refresh_button)
        left_layout.addWidget(self.list_widget, stretch=1)
        left_layout.addWidget(self.list_empty_label)

        self.player_widget = PlayerWidget()

        self.content_widget = QWidget()
        content_layout = QHBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(left_panel)
        content_layout.addWidget(self.player_widget, stretch=1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)

        self._update_empty_state()

    # -- standard page protocol -------------------------------------------

    def set_repo(self, project, repo, workspace_root: str) -> None:
        self._project_id = project.id if project is not None else None
        self._repo_id = repo.id if repo is not None else None
        self._reload_videos()

    # -- video list ---------------------------------------------------------

    def _reload_videos(self) -> None:
        self.list_widget.clear()
        self.player_widget.clear_video()
        self._video_root = None
        if self._project_id and self._repo_id:
            self._video_root = video_path_store.resolve_video_root(self._api, self._project_id, self._repo_id)
        self._update_empty_state()
        if self._video_root is None or not self._video_root.is_dir():
            return

        videos = sorted(
            (p for p in self._video_root.iterdir() if p.is_file() and p.suffix.lower() in _VIDEO_EXTENSIONS),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for video_path in videos:
            item = QListWidgetItem(video_path.name)
            item.setData(Qt.UserRole, str(video_path))
            self.list_widget.addItem(item)
            self._thumbnail_loader.request(video_path)
        self.list_empty_label.setVisible(not videos)
        self.list_widget.setVisible(bool(videos))

    def _on_thumbnail_ready(self, video_path_str: str, pixmap: QPixmap) -> None:
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item.data(Qt.UserRole) == video_path_str:
                item.setIcon(QIcon(pixmap))
                break

    def _update_empty_state(self) -> None:
        if not self._project_id or not self._repo_id:
            self.empty_label.setText("Select a repo to see this information.")
            show_exclusive(self.empty_label, self.content_widget)
            return
        if self._video_root is None:
            self.empty_label.setText(
                "No video library configured for this repo yet — set one in Repository Setting > UkoreShot."
            )
            show_exclusive(self.empty_label, self.content_widget)
            return
        show_exclusive(self.content_widget, self.empty_label)

    def _on_current_item_changed(self, current: QListWidgetItem, _previous: QListWidgetItem) -> None:
        if current is None:
            self.player_widget.clear_video()
            return
        self.player_widget.load_video(Path(current.data(Qt.UserRole)))
