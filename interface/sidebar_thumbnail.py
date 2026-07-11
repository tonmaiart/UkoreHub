from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

_FALLBACK_BACKGROUND = QColor("#232428")


class ThumbnailBackgroundWidget(QWidget):
    """Paints a repo's thumbnail image as a background, center-cropped to
    fill the widget, with a dark gradient fading up from the bottom so text
    laid over it (via a child layout) stays legible."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: QPixmap | None = None

    def set_image(self, path: Path | None) -> None:
        if path is not None and Path(path).exists():
            pixmap = QPixmap(str(path))
            self._pixmap = pixmap if not pixmap.isNull() else None
        else:
            self._pixmap = None
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        rect = self.rect()

        if self._pixmap is not None:
            scaled = self._pixmap.scaled(
                rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (scaled.width() - rect.width()) // 2
            y = (scaled.height() - rect.height()) // 2
            painter.drawPixmap(rect, scaled, QRect(x, y, rect.width(), rect.height()))
        else:
            painter.fillRect(rect, _FALLBACK_BACKGROUND)

        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.55, QColor(0, 0, 0, 110))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 200))
        painter.fillRect(rect, gradient)

        painter.end()
        super().paintEvent(event)
