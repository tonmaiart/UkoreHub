from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

BANNER_HEIGHT = 140


class _ThumbnailBanner(QWidget):
    """The repo thumbnail, full-bleed and never rounded (fill-crop, not
    letterboxed) across the top of the Sidebar. No text overlay — the repo
    name is shown once, on ActiveRepoWidget's select_button below, rather
    than duplicated here."""

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
    it, a full-width "Project / Repo" button that opens the repo picker —
    the button is the only place the repo's name is shown here, so the
    banner itself carries no text overlay."""

    repo_picker_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.banner = _ThumbnailBanner()
        self.select_button = QPushButton("No Repo Selected")
        self.select_button.setObjectName("activeRepoSelectButton")
        self.select_button.clicked.connect(self.repo_picker_requested.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.banner)
        layout.addWidget(self.select_button)

    def set_active_labels(self, repo_name: str | None, project_name: str | None = None) -> None:
        if repo_name and project_name:
            self.select_button.setText(f"{project_name} / {repo_name}  ...")
        else:
            self.select_button.setText(repo_name or "No Repo Selected")

    def set_thumbnail(self, path: Path | None) -> None:
        pixmap = QPixmap(str(path)) if path and Path(path).exists() else None
        if pixmap is not None and pixmap.isNull():
            pixmap = None
        self.banner.set_pixmap(pixmap)
