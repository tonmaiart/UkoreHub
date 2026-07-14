from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPixmap


def circular_pixmap(pixmap: QPixmap, size: int) -> QPixmap:
    """Center-crops `pixmap` to a `size`x`size` square, then clips it to a
    circle. Used for avatar-style images (GitHub login avatar) — not for
    full-bleed background art."""
    scaled = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    x = max(0, (scaled.width() - size) // 2)
    y = max(0, (scaled.height() - size) // 2)
    cropped = scaled.copy(x, y, size, size)

    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addEllipse(QRectF(0, 0, size, size))
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, cropped)
    painter.end()
    return result
