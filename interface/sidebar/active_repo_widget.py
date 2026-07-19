from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

BANNER_HEIGHT = 140


class _ThumbnailBanner(QWidget):
    """The repo thumbnail, full-bleed and never rounded (fill-crop, not
    letterboxed) across the top of the Sidebar. No text overlay — the repo
    name is shown once, on ActiveRepoWidget's name_label below, rather than
    duplicated here."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(BANNER_HEIGHT)
        self._pixmap: QPixmap | None = None

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event) -> None:
        if self._pixmap is not None and not self._pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = max(0, (scaled.width() - self.width()) // 2)
            y = max(0, (scaled.height() - self.height()) // 2)
            painter.drawPixmap(self.rect(), scaled, QRect(x, y, self.width(), self.height()))
            painter.end()
        super().paintEvent(event)


class ActiveRepoWidget(QWidget):
    """Top of the Sidebar: the repo thumbnail banner and, directly beneath
    it, a plain label naming the active Project/Repo — display-only, no
    click-to-open-picker (removed 2026-07-15 along with the "Select
    Repo..." dialog flow for normal operation). Switching the active repo
    now only happens by clicking a node in Project Editor's always-visible
    graph panel, see plugins/studio/project_editor/."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.banner = _ThumbnailBanner()
        self.name_label = QLabel("No Repo Selected")
        self.name_label.setObjectName("activeRepoNameLabel")
        self.name_label.setWordWrap(True)
        self.name_label.setContentsMargins(10, 8, 10, 8)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.banner)
        layout.addWidget(self.name_label)

    def set_active_labels(self, repo_name: str | None, project_name: str | None = None) -> None:
        if repo_name and project_name:
            self.name_label.setText(f"{project_name} / {repo_name}")
        else:
            self.name_label.setText(repo_name or "No Repo Selected")

    def set_thumbnail(self, path: Path | None) -> None:
        pixmap = QPixmap(str(path)) if path and Path(path).exists() else None
        if pixmap is not None and pixmap.isNull():
            pixmap = None
        self.banner.set_pixmap(pixmap)
