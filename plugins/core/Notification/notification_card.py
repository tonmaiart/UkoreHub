from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from core.events.notification_bus import NotificationEntry

_DATETIME_FORMAT = "%Y-%m-%d %H:%M"
_ICON_SIZE = 28


class NotificationCard(QFrame):
    """The one card template every producer's notification renders through
    (interface.theme.py's QFrame#notificationCard idiom, same shape as
    _VideoCard elsewhere in this codebase): icon, label, date/time,
    and an optional click action. Only clickable (pointer cursor + hover
    highlight via the [clickable="true"] QSS property) when the entry
    actually has an on_click."""

    clicked = Signal()

    def __init__(self, entry: NotificationEntry, parent=None):
        super().__init__(parent)
        self.setObjectName("notificationCard")
        self.setFrameShape(QFrame.StyledPanel)
        self._entry = entry

        icon_label = QLabel()
        icon_label.setFixedSize(_ICON_SIZE, _ICON_SIZE)
        if entry.icon_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(entry.icon_bytes)
            icon_label.setPixmap(
                pixmap.scaled(_ICON_SIZE, _ICON_SIZE, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            )
        elif entry.icon_path is not None and entry.icon_path.exists():
            icon_label.setPixmap(QIcon(str(entry.icon_path)).pixmap(_ICON_SIZE, _ICON_SIZE))

        text_label = QLabel(entry.label)
        text_label.setWordWrap(True)
        text_label.setProperty("cardTitle", True)

        time_label = QLabel(entry.timestamp.strftime(_DATETIME_FORMAT))
        time_label.setProperty("secondary", True)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.addWidget(text_label)
        text_layout.addWidget(time_label)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        layout.addWidget(icon_label)
        layout.addLayout(text_layout, 1)

        if entry.on_click is not None:
            self.setProperty("clickable", True)
            self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        if self._entry.on_click is not None:
            self.clicked.emit()
            self._entry.on_click()
        super().mousePressEvent(event)
