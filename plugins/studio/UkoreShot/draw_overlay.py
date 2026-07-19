from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPaintEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

_UNDO_STACK_LIMIT = 20
_ERASER_RADIUS = 0.03  # normalized widget-space distance


@dataclass
class Stroke:
    color: str  # "#rrggbb"
    width: int
    points: list[tuple[float, float]] = field(default_factory=list)  # normalized 0-1 widget space

    def to_dict(self) -> dict:
        return {"color": self.color, "width": self.width, "points": [list(p) for p in self.points]}

    @classmethod
    def from_dict(cls, data: dict) -> "Stroke":
        return cls(
            color=data.get("color", "#ff3b30"),
            width=int(data.get("width", 4)),
            points=[tuple(p) for p in data.get("points", [])],
        )


class DrawOverlay(QWidget):
    """Transparent freehand-drawing canvas stacked on top of the video
    surface (see player_widget.py's QStackedLayout) — one stroke list per
    frame index, deliberately simple ("แบบโง่", per the user's own
    description of the feature): fixed-shape freehand pen only, no vector
    editing after the fact beyond a whole-stroke eraser and a
    snapshot-based per-frame undo stack. Undo history is NOT persisted —
    only the final stroke list for a frame is ever saved (see
    comment_store.py) — and resets whenever a different frame is loaded,
    since undo only ever makes sense within one frame's own editing
    session. Strokes are only ever shown for the exact frame index
    currently loaded (see load_frame) so scrubbing between frames doesn't
    smear one frame's drawing onto another."""

    strokesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._strokes: list[Stroke] = []
        self._undo_stack: list[list[Stroke]] = []
        self._active_points: list[tuple[float, float]] = []
        self._color = "#ff3b30"
        self._brush_width = 4
        self._eraser = False
        self._drawing_enabled = True

    # -- toolbar-facing API -------------------------------------------------

    def set_color(self, color: QColor) -> None:
        self._color = color.name()

    def set_brush_width(self, width: int) -> None:
        self._brush_width = max(1, width)

    def set_eraser_mode(self, enabled: bool) -> None:
        self._eraser = enabled

    def set_drawing_enabled(self, enabled: bool) -> None:
        """Drawing only makes sense while playback is paused on one exact
        frame (see PlayerWidget._set_paused_state) — disabled during
        playback so a stray click while the video is moving doesn't start
        a stroke against a frame index that's about to change."""
        self._drawing_enabled = enabled

    def load_frame(self, strokes: list[Stroke]) -> None:
        """Swaps in the persisted stroke list for whichever frame index is
        now current."""
        self._strokes = list(strokes)
        self._undo_stack = []
        self._active_points = []
        self.update()

    def current_strokes(self) -> list[Stroke]:
        return list(self._strokes)

    def clear_frame(self) -> None:
        if not self._strokes:
            return
        self._push_undo()
        self._strokes = []
        self.update()
        self.strokesChanged.emit()

    def undo(self) -> None:
        if not self._undo_stack:
            return
        self._strokes = self._undo_stack.pop()
        self.update()
        self.strokesChanged.emit()

    # -- stroke capture -------------------------------------------------

    def _push_undo(self) -> None:
        self._undo_stack.append(list(self._strokes))
        if len(self._undo_stack) > _UNDO_STACK_LIMIT:
            self._undo_stack.pop(0)

    def _normalized(self, pos: QPointF) -> tuple[float, float]:
        w = max(1, self.width())
        h = max(1, self.height())
        return pos.x() / w, pos.y() / h

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._drawing_enabled or event.button() != Qt.LeftButton:
            return
        self._push_undo()
        point = self._normalized(event.position())
        if self._eraser:
            self._erase_near(point)
        else:
            self._active_points = [point]
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._drawing_enabled or not (event.buttons() & Qt.LeftButton):
            return
        point = self._normalized(event.position())
        if self._eraser:
            self._erase_near(point)
        else:
            self._active_points.append(point)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self._drawing_enabled or event.button() != Qt.LeftButton:
            return
        if not self._eraser and len(self._active_points) > 1:
            self._strokes.append(Stroke(color=self._color, width=self._brush_width, points=self._active_points))
        self._active_points = []
        self.update()
        self.strokesChanged.emit()

    def _erase_near(self, point: tuple[float, float]) -> None:
        """Whole-stroke eraser: removes any stroke with at least one point
        within _ERASER_RADIUS (normalized widget space) of the cursor —
        simple by design, matching the "dumb" freehand tool this is, not a
        pixel-level eraser."""
        px, py = point
        remaining = [
            s
            for s in self._strokes
            if not any((qx - px) ** 2 + (qy - py) ** 2 <= _ERASER_RADIUS * _ERASER_RADIUS for qx, qy in s.points)
        ]
        if len(remaining) != len(self._strokes):
            self._strokes = remaining

    # -- painting -------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for stroke in self._strokes:
            self._paint_points(painter, stroke.points, QColor(stroke.color), stroke.width)
        if self._active_points and not self._eraser:
            self._paint_points(painter, self._active_points, QColor(self._color), self._brush_width)
        painter.end()

    def _paint_points(self, painter: QPainter, points: list[tuple[float, float]], color: QColor, width: int) -> None:
        if len(points) < 2:
            return
        w = self.width()
        h = self.height()
        path = QPainterPath()
        path.moveTo(points[0][0] * w, points[0][1] * h)
        for x, y in points[1:]:
            path.lineTo(x * w, y * h)
        painter.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)
