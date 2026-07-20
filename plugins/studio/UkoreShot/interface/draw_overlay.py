from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPaintEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

# The app's own top-level core/ package, NOT this plugin's sibling
# plugins.studio.UkoreShot.core package (same name, different package,
# resolved unambiguously since this is an absolute import) — see
# plugins/studio/UkoreShot/core/README.md's note on this.
from core.extensibility import debug_log

_DEBUG_SOURCE = "UkoreShot.Draw"
debug_log.register_source(_DEBUG_SOURCE)

_UNDO_STACK_LIMIT = 20
_MIN_TOOL_SIZE = 1
_MAX_TOOL_SIZE = 60
_RESIZE_PIXELS_PER_UNIT = 4  # mouse-drag sensitivity for the "F" resize gesture
_TEXT_BOX_WIDTH = 160
_TEXT_BOX_HEIGHT = 80
_DEFAULT_TEXT_BOX_POS = (0.1, 0.1)  # fallback only, for a saved text box missing x/y

TOOL_BRUSH = "brush"
TOOL_ERASER = "eraser"
TOOL_TEXT = "text"


class _DragHandle(QLabel):
    """The only part of a _TextBoxItem that drags the box — keeps dragging
    from fighting with placing a text cursor in the text field below it."""

    def __init__(self, box: "_TextBoxItem", parent=None):
        super().__init__("⋮⋮", parent)
        self._box = box
        self.setCursor(Qt.SizeAllCursor)
        self.setProperty("secondary", True)
        self._drag_start: QPoint | None = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_start = event.globalPosition().toPoint() - self._box.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is not None and event.buttons() & Qt.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_start
            container = self._box.parentWidget()
            if container is not None:
                max_x = max(0, container.width() - self._box.width())
                max_y = max(0, container.height() - self._box.height())
                new_pos.setX(min(max(0, new_pos.x()), max_x))
                new_pos.setY(min(max(0, new_pos.y()), max_y))
            self._box.move(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._drag_start is not None:
            self._drag_start = None
            self._box.changed.emit()
        super().mouseReleaseEvent(event)


class _TextBoxItem(QFrame):
    """One draggable, editable text annotation pinned to a frame — however
    many an Animator wants (DrawOverlay.add_text_box, one per click).
    `norm_pos` (top-left corner, 0-1) is the same widget-space
    normalization Stroke.points already uses, so a box tracks correctly if
    the player is resized (see DrawOverlay.resizeEvent)."""

    changed = Signal()
    deleteRequested = Signal(object)

    def __init__(self, text: str, norm_pos: tuple[float, float], parent=None):
        super().__init__(parent)
        self.norm_pos = norm_pos
        self.setObjectName("textBoxItem")
        self.setFrameShape(QFrame.StyledPanel)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(_TEXT_BOX_WIDTH, _TEXT_BOX_HEIGHT)

        delete_button = QPushButton("×")
        delete_button.setFixedSize(18, 18)
        delete_button.clicked.connect(lambda: self.deleteRequested.emit(self))

        handle_row = QHBoxLayout()
        handle_row.setContentsMargins(4, 2, 4, 2)
        handle_row.addWidget(_DragHandle(self), stretch=1)
        handle_row.addWidget(delete_button)

        self.text_edit = QPlainTextEdit(text)
        self.text_edit.textChanged.connect(self.changed.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 4, 4)
        layout.setSpacing(2)
        layout.addLayout(handle_row)
        layout.addWidget(self.text_edit, stretch=1)

    def text(self) -> str:
        return self.text_edit.toPlainText()


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
    surface (see player_widget.py's _VideoStack) — one stroke list per
    frame index, deliberately simple ("แบบโง่", per the user's own
    description of the feature): fixed-shape freehand pen only, no vector
    editing after the fact beyond a whole-stroke eraser and a
    snapshot-based per-frame undo/redo stack pair (undo() pushes the
    current state onto _redo_stack before popping _undo_stack, and vice
    versa for redo(); any new action — a new stroke, clear_frame — clears
    _redo_stack via _push_undo, the same "new edit invalidates redo
    history" rule every undo/redo system uses). Undo/redo history is NOT
    persisted — only the final stroke list for a frame is ever saved (see
    comment_store.py) — and resets whenever a different frame is loaded,
    since undo/redo only ever makes sense within one frame's own editing
    session. Strokes are only ever shown for the exact frame index
    currently loaded (see load_frame) so scrubbing between frames doesn't
    smear one frame's drawing onto another. Text boxes are not part of
    this undo/redo stack — only strokes are (matches the original undo
    feature's scope, not expanded here).

    _TextBoxItem children ride along on the same per-frame swap (load_frame
    tears down and rebuilds them same as strokes) but are real interactive
    QWidgets, not painted like strokes — see _TextBoxItem/​_DragHandle above."""

    strokesChanged = Signal()
    textBoxesChanged = Signal()
    # Emitted only when the "F" resize gesture (below) changes the size —
    # NOT when set_brush_width() is called from the toolbar's Size slider,
    # which would just be an echo of what the slider already knows. Lets
    # PlayerWidget keep that slider's displayed value in sync when a size
    # change instead comes from the keyboard gesture.
    toolSizeChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Belt-and-suspenders: player_widget.py's _VideoSurface (2026-07-20)
        # already isn't a native window, so this shouldn't be load-bearing
        # anymore — but it was the first (insufficient on its own) attempt
        # at fixing "brush doesn't respond to mouse input at all" when the
        # sibling below this overlay was still QVideoWidget (a real native
        # window, which OS-level Z-ordering/hit-testing always won
        # regardless of any attribute set here). Left on since it's
        # harmless and still correct in spirit for a translucent overlay.
        self.setAttribute(Qt.WA_AlwaysStackOnTop)
        self.setMouseTracking(True)  # so mouseMoveEvent fires without a button held, for the hover-size indicator
        # StrongFocus + grabbing focus on hover (enterEvent below) so the
        # "F" resize gesture works as soon as the cursor is over the
        # canvas, without needing an explicit click first — mirrors how a
        # 3D viewport typically reacts to hover + a single keypress.
        self.setFocusPolicy(Qt.StrongFocus)
        self._strokes: list[Stroke] = []
        self._undo_stack: list[list[Stroke]] = []
        self._redo_stack: list[list[Stroke]] = []
        self._active_points: list[tuple[float, float]] = []
        self._color = "#ff3b30"
        # One "tool size" (pixel radius/width) shared by both the brush
        # (stroke width) and the eraser (hit-test radius) — the "F"
        # resize gesture and the toolbar's Size slider both just adjust
        # this one value, whichever tool happens to be active.
        self._brush_width = 4
        # Exactly one of TOOL_BRUSH/TOOL_ERASER/TOOL_TEXT at a time — the
        # single source of truth every mouse handler branches on, so the
        # three tools never act simultaneously (fixed 2026-07-20: Text
        # used to be a one-shot action that left Brush's drawing active
        # underneath, so repositioning a text box could also draw a
        # stroke at the same time).
        self._tool = TOOL_BRUSH
        self._drawing_enabled = True
        self._text_boxes: list[_TextBoxItem] = []
        self._hover_pos: QPointF | None = None
        self._resizing = False
        self._resize_start_pos: QPointF | None = None
        self._resize_start_value: int | None = None

    # -- toolbar-facing API -------------------------------------------------

    def set_color(self, color: QColor) -> None:
        self._color = color.name()

    def set_brush_width(self, width: int) -> None:
        self._brush_width = max(_MIN_TOOL_SIZE, min(_MAX_TOOL_SIZE, width))
        self.update()

    def set_tool(self, tool: str) -> None:
        """tool is one of TOOL_BRUSH/TOOL_ERASER/TOOL_TEXT — exclusive,
        called from whichever toolbox button just became checked (see
        player_widget.py). Abandons any in-progress stroke so switching
        tools mid-drag can't leave a half-drawn stroke dangling."""
        self._tool = tool
        self._active_points = []
        self.update()

    def set_drawing_enabled(self, enabled: bool) -> None:
        """Drawing only makes sense while playback is paused on one exact
        frame (see PlayerWidget._set_paused_state) — disabled during
        playback so a stray click while the video is moving doesn't start
        a stroke against a frame index that's about to change."""
        self._drawing_enabled = enabled

    def load_frame(self, strokes: list[Stroke], text_boxes: list[dict] | None = None) -> None:
        """Swaps in the persisted stroke list and text boxes for whichever
        frame index is now current."""
        self._strokes = list(strokes)
        self._undo_stack = []
        self._redo_stack = []
        self._active_points = []
        for box in self._text_boxes:
            box.setParent(None)
            box.deleteLater()
        self._text_boxes = []
        for data in text_boxes or []:
            pos = (data.get("x", _DEFAULT_TEXT_BOX_POS[0]), data.get("y", _DEFAULT_TEXT_BOX_POS[1]))
            self._add_text_box(data.get("text", ""), pos)
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
        self._redo_stack.append(list(self._strokes))
        self._strokes = self._undo_stack.pop()
        self.update()
        self.strokesChanged.emit()

    def redo(self) -> None:
        if not self._redo_stack:
            return
        self._undo_stack.append(list(self._strokes))
        self._strokes = self._redo_stack.pop()
        self.update()
        self.strokesChanged.emit()

    # -- text boxes -------------------------------------------------------

    def _add_text_box(self, text: str, norm_pos: tuple[float, float]) -> None:
        box = _TextBoxItem(text, norm_pos, parent=self)
        box.changed.connect(lambda b=box: self._on_text_box_changed(b))
        box.deleteRequested.connect(self._remove_text_box)
        box.move(round(norm_pos[0] * self.width()), round(norm_pos[1] * self.height()))
        box.show()
        box.raise_()
        self._text_boxes.append(box)

    def _remove_text_box(self, box: "_TextBoxItem") -> None:
        if box in self._text_boxes:
            self._text_boxes.remove(box)
        box.setParent(None)
        box.deleteLater()
        self.textBoxesChanged.emit()

    def _on_text_box_changed(self, box: "_TextBoxItem") -> None:
        box.norm_pos = self._normalized(QPointF(box.pos()))
        self.textBoxesChanged.emit()

    def current_text_boxes(self) -> list[dict]:
        return [{"text": b.text(), "x": b.norm_pos[0], "y": b.norm_pos[1]} for b in self._text_boxes]

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        debug_log.log(_DEBUG_SOURCE, f"resizeEvent, new size={self.size()}, visible={self.isVisible()}")
        for box in self._text_boxes:
            box.move(round(box.norm_pos[0] * self.width()), round(box.norm_pos[1] * self.height()))

    # -- "F" resize gesture -------------------------------------------------

    def enterEvent(self, event) -> None:
        self.setFocus()
        super().enterEvent(event)

    def keyPressEvent(self, event) -> None:
        if (
            event.key() == Qt.Key_F
            and self._drawing_enabled
            and self._hover_pos is not None
            and self._tool != TOOL_TEXT
        ):
            if self._resizing:
                self._end_resize(commit=True)
            else:
                self._start_resize()
            return
        if event.key() == Qt.Key_Escape and self._resizing:
            self._end_resize(commit=False)
            return
        super().keyPressEvent(event)

    def _start_resize(self) -> None:
        self._resizing = True
        self._resize_start_pos = self._hover_pos
        self._resize_start_value = self._brush_width
        debug_log.log(_DEBUG_SOURCE, f"resize gesture started at size={self._brush_width}")

    def _end_resize(self, *, commit: bool) -> None:
        if not commit and self._resize_start_value is not None:
            self._brush_width = self._resize_start_value
            self.toolSizeChanged.emit(self._brush_width)
        self._resizing = False
        self._resize_start_pos = None
        self._resize_start_value = None
        self.update()
        debug_log.log(_DEBUG_SOURCE, f"resize gesture ended, commit={commit}, size={self._brush_width}")

    # -- stroke capture -------------------------------------------------

    def _push_undo(self) -> None:
        self._undo_stack.append(list(self._strokes))
        if len(self._undo_stack) > _UNDO_STACK_LIMIT:
            self._undo_stack.pop(0)
        self._redo_stack.clear()  # a new action invalidates any redo history, standard undo/redo semantics

    def _normalized(self, pos: QPointF) -> tuple[float, float]:
        w = max(1, self.width())
        h = max(1, self.height())
        return pos.x() / w, pos.y() / h

    def mousePressEvent(self, event: QMouseEvent) -> None:
        debug_log.log(
            _DEBUG_SOURCE,
            f"mousePressEvent at {event.position()}, drawing_enabled={self._drawing_enabled}, button={event.button()}",
        )
        if self._resizing:
            if event.button() == Qt.LeftButton:
                self._end_resize(commit=True)
            return
        if not self._drawing_enabled or event.button() != Qt.LeftButton:
            return
        if self._tool == TOOL_TEXT:
            self._add_text_box("", self._normalized(event.position()))
            self.textBoxesChanged.emit()
            return
        self._push_undo()
        point = self._normalized(event.position())
        if self._tool == TOOL_ERASER:
            self._erase_near(point)
        else:
            self._active_points = [point]
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        debug_log.log(_DEBUG_SOURCE, f"mouseMoveEvent at {event.position()}, buttons={event.buttons()}")
        self._hover_pos = event.position()
        if self._resizing:
            delta = event.position().x() - self._resize_start_pos.x()
            new_size = round(self._resize_start_value + delta / _RESIZE_PIXELS_PER_UNIT)
            self._brush_width = max(_MIN_TOOL_SIZE, min(_MAX_TOOL_SIZE, new_size))
            self.toolSizeChanged.emit(self._brush_width)
            self.update()
            return
        if self._tool == TOOL_TEXT:
            self.update()
            return
        if not self._drawing_enabled or not (event.buttons() & Qt.LeftButton):
            self.update()
            return
        point = self._normalized(event.position())
        if self._tool == TOOL_ERASER:
            self._erase_near(point)
        else:
            self._active_points.append(point)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._resizing or self._tool == TOOL_TEXT:
            return
        if not self._drawing_enabled or event.button() != Qt.LeftButton:
            return
        if self._tool == TOOL_BRUSH and len(self._active_points) > 1:
            self._strokes.append(Stroke(color=self._color, width=self._brush_width, points=self._active_points))
        self._active_points = []
        self.update()
        self.strokesChanged.emit()

    def leaveEvent(self, event) -> None:
        self._hover_pos = None
        self.update()
        super().leaveEvent(event)

    def _erase_near(self, point: tuple[float, float]) -> None:
        """Whole-stroke eraser: removes any stroke with at least one point
        within the current tool size (converted to normalized widget-space
        distance) of the cursor — simple by design, matching the "dumb"
        freehand tool this is, not a pixel-level eraser."""
        px, py = point
        radius = self._brush_width / max(1, self.width())
        remaining = [
            s
            for s in self._strokes
            if not any((qx - px) ** 2 + (qy - py) ** 2 <= radius * radius for qx, qy in s.points)
        ]
        if len(remaining) != len(self._strokes):
            self._strokes = remaining

    # -- painting -------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for stroke in self._strokes:
            self._paint_points(painter, stroke.points, QColor(stroke.color), stroke.width)
        if self._active_points and self._tool == TOOL_BRUSH:
            self._paint_points(painter, self._active_points, QColor(self._color), self._brush_width)
        self._paint_hover_indicator(painter)
        painter.end()

    def _paint_hover_indicator(self, painter: QPainter) -> None:
        """A hollow circle following the cursor showing the exact brush
        (or eraser) size before a stroke is even started — hidden while
        drawing is disabled (video playing), the cursor isn't over the
        canvas at all (leaveEvent), or the Text tool is active (size
        doesn't apply to placing a text box)."""
        if self._hover_pos is None or not self._drawing_enabled or self._tool == TOOL_TEXT:
            debug_log.log(
                _DEBUG_SOURCE,
                f"hover indicator skipped: hover_pos={self._hover_pos}, "
                f"drawing_enabled={self._drawing_enabled}, tool={self._tool}",
            )
            return
        if self._tool == TOOL_ERASER:
            # _erase_near's hit-test radius (normalized) is
            # self._brush_width / self.width() — converting that back to
            # pixels for painting is just self._brush_width again.
            radius = max(1.0, float(self._brush_width))
            color = QColor(255, 255, 255, 200)
        else:
            radius = max(1.0, self._brush_width / 2)
            color = QColor(self._color)
            color.setAlpha(200)
        painter.setPen(QPen(color, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(self._hover_pos, radius, radius)

    def _paint_points(self, painter: QPainter, points: list[tuple[float, float]], color: QColor, width: int) -> None:
        paint_stroke_points(painter, points, color, width, self.width(), self.height())


def paint_stroke_points(
    painter: QPainter, points: list[tuple[float, float]], color: QColor, width: int, w: int, h: int
) -> None:
    """Module-level so ReadOnlyCommentOverlay (below) can paint a stroke
    pixel-identically to how DrawOverlay._paint_points draws it, without
    either duplicating the math or depending on the other class."""
    if len(points) < 2:
        return
    path = QPainterPath()
    path.moveTo(points[0][0] * w, points[0][1] * h)
    for x, y in points[1:]:
        path.lineTo(x * w, y * h)
    painter.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawPath(path)


class ReadOnlyCommentOverlay(QWidget):
    """View-mode-only, read-only rendering of a frame's saved strokes and
    text boxes on top of the video — no mouse handling, no editing, no
    toolbox. Added 2026-07-20 so the plain viewing page can see what was
    commented without opening the full Edit Video dialog; visibility is
    toggled by player_widget.py's own button.
    WA_TransparentForMouseEvents so it can never itself become a second
    thing standing between the mouse and anything else on the video (the
    exact class of bug bug-history/2026-07-20-draw-overlay-native-video-widget.md
    and 2026-07-20-text-tool-drew-strokes-simultaneously.md were about —
    even though this widget has nothing interactive of its own, the habit
    is worth keeping)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._strokes: list[Stroke] = []
        self._text_boxes: list[dict] = []

    def set_frame(self, strokes: list[Stroke], text_boxes: list[dict]) -> None:
        self._strokes = strokes
        self._text_boxes = text_boxes
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        for stroke in self._strokes:
            paint_stroke_points(painter, stroke.points, QColor(stroke.color), stroke.width, w, h)
        for box in self._text_boxes:
            self._paint_text_box(painter, box, w, h)
        painter.end()

    def _paint_text_box(self, painter: QPainter, box: dict, w: int, h: int) -> None:
        text = box.get("text", "")
        if not text:
            return
        rect = QRectF(box.get("x", 0.0) * w, box.get("y", 0.0) * h, _TEXT_BOX_WIDTH, _TEXT_BOX_HEIGHT)
        painter.setPen(QPen(QColor("#5865f2"), 1))
        painter.setBrush(QColor(43, 45, 49, 220))
        painter.drawRoundedRect(rect, 4, 4)
        painter.setPen(QColor("white"))
        painter.drawText(rect.adjusted(6, 4, -6, -4), Qt.TextWordWrap, text)
