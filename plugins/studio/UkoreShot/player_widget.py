from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QColor
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedLayout,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from plugins.studio.UkoreShot import comment_store
from plugins.studio.UkoreShot.draw_overlay import DrawOverlay, Stroke

_DEFAULT_FPS = 24


class PlayerWidget(QWidget):
    """Video playback + frame-by-frame grease-pencil drawing/comment
    review, for whichever video UkoreShotPage's list has selected. Frame
    stepping/indexing is an FPS-based approximation
    (round(position_ms / 1000 * fps)) — QMediaPlayer has no native
    frame-accurate API for arbitrary containers; confirmed with the user as
    an acceptable simplification ("แบบโง่") rather than something to solve
    precisely. `fps_spin` lets an Animator match it to the actual playblast
    FPS if 24 isn't right for a given shot."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._video_path: Path | None = None
        self._frames: dict = {"frames": {}}
        self._current_frame_index = 0
        self._scrubbing = False

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)

        self.draw_overlay = DrawOverlay()
        self.draw_overlay.strokesChanged.connect(self._on_strokes_changed)

        video_stack_widget = QWidget()
        video_stack = QStackedLayout(video_stack_widget)
        video_stack.setStackingMode(QStackedLayout.StackAll)
        video_stack.addWidget(self.video_widget)
        video_stack.addWidget(self.draw_overlay)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self._on_play_clicked)
        self.prev_frame_button = QPushButton("<")
        self.prev_frame_button.clicked.connect(lambda: self._step_frame(-1))
        self.next_frame_button = QPushButton(">")
        self.next_frame_button.clicked.connect(lambda: self._step_frame(1))
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.sliderPressed.connect(self._on_slider_pressed)
        self.position_slider.sliderReleased.connect(self._on_slider_released)
        self.position_slider.sliderMoved.connect(self._on_slider_moved)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(_DEFAULT_FPS)
        self.fps_spin.setPrefix("FPS ")

        transport_row = QHBoxLayout()
        transport_row.addWidget(self.play_button)
        transport_row.addWidget(self.prev_frame_button)
        transport_row.addWidget(self.next_frame_button)
        transport_row.addWidget(self.position_slider, stretch=1)
        transport_row.addWidget(self.fps_spin)

        self.color_button = QPushButton("Color")
        self.color_button.clicked.connect(self._on_pick_color)
        self._current_color = QColor("#ff3b30")
        self._update_color_button()
        self.brush_slider = QSlider(Qt.Horizontal)
        self.brush_slider.setRange(1, 20)
        self.brush_slider.setValue(4)
        self.brush_slider.setMaximumWidth(120)
        self.brush_slider.valueChanged.connect(self.draw_overlay.set_brush_width)
        self.eraser_check = QCheckBox("Eraser")
        self.eraser_check.toggled.connect(self.draw_overlay.set_eraser_mode)
        self.clear_button = QPushButton("Clear Frame")
        self.clear_button.clicked.connect(self.draw_overlay.clear_frame)
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self.draw_overlay.undo)

        draw_row = QHBoxLayout()
        draw_row.addWidget(QLabel("Draw:"))
        draw_row.addWidget(self.color_button)
        draw_row.addWidget(QLabel("Size"))
        draw_row.addWidget(self.brush_slider)
        draw_row.addWidget(self.eraser_check)
        draw_row.addWidget(self.clear_button)
        draw_row.addWidget(self.undo_button)
        draw_row.addStretch()

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Comment on this frame...")
        self.note_edit.setMaximumHeight(80)
        self.note_edit.textChanged.connect(self._on_note_changed)

        layout = QVBoxLayout(self)
        layout.addWidget(video_stack_widget, stretch=1)
        layout.addLayout(transport_row)
        layout.addLayout(draw_row)
        layout.addWidget(self.note_edit)

        self.draw_overlay.set_color(self._current_color)
        self._set_paused_state(True)

    # -- loading --------------------------------------------------------

    def load_video(self, video_path: Path) -> None:
        self._video_path = video_path
        self._frames = comment_store.load(video_path)
        self.player.setSource(QUrl.fromLocalFile(str(video_path)))
        self.player.pause()
        self._current_frame_index = 0
        self._load_current_frame()

    def clear_video(self) -> None:
        self._video_path = None
        self.player.stop()
        self.player.setSource(QUrl())
        self._frames = {"frames": {}}
        self.draw_overlay.load_frame([])
        self.note_edit.blockSignals(True)
        self.note_edit.clear()
        self.note_edit.blockSignals(False)

    # -- transport --------------------------------------------------------

    def _fps(self) -> int:
        return self.fps_spin.value()

    def _on_play_clicked(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self._set_paused_state(False)
            self.player.play()

    def _set_paused_state(self, paused: bool) -> None:
        self.play_button.setText("Play" if paused else "Pause")
        self.draw_overlay.set_drawing_enabled(paused)

    def _on_duration_changed(self, duration_ms: int) -> None:
        self.position_slider.setRange(0, max(0, duration_ms))

    def _on_position_changed(self, position_ms: int) -> None:
        if self.player.playbackState() != QMediaPlayer.PlayingState:
            self._set_paused_state(True)
        if not self._scrubbing:
            self.position_slider.blockSignals(True)
            self.position_slider.setValue(position_ms)
            self.position_slider.blockSignals(False)
        frame_index = round(position_ms / 1000 * self._fps())
        if frame_index != self._current_frame_index:
            self._current_frame_index = frame_index
            self._load_current_frame()

    def _on_slider_pressed(self) -> None:
        self._scrubbing = True

    def _on_slider_released(self) -> None:
        self._scrubbing = False
        self.player.setPosition(self.position_slider.value())
        self.player.pause()

    def _on_slider_moved(self, value: int) -> None:
        self.player.setPosition(value)

    def _step_frame(self, delta: int) -> None:
        self.player.pause()
        frame_ms = 1000 / self._fps()
        new_position = max(0, self.player.position() + delta * frame_ms)
        self.player.setPosition(round(new_position))

    # -- per-frame drawing/comment persistence ---------------------------

    def _load_current_frame(self) -> None:
        frame_entry = self._frames.get("frames", {}).get(str(self._current_frame_index), {})
        strokes = [Stroke.from_dict(s) for s in frame_entry.get("strokes", [])]
        self.draw_overlay.load_frame(strokes)
        self.note_edit.blockSignals(True)
        self.note_edit.setPlainText(frame_entry.get("note", ""))
        self.note_edit.blockSignals(False)

    def _on_strokes_changed(self) -> None:
        self._save_current_frame(strokes=self.draw_overlay.current_strokes())

    def _on_note_changed(self) -> None:
        self._save_current_frame(note=self.note_edit.toPlainText())

    def _save_current_frame(self, *, strokes: list[Stroke] | None = None, note: str | None = None) -> None:
        if self._video_path is None:
            return
        frames = self._frames.setdefault("frames", {})
        key = str(self._current_frame_index)
        entry = dict(frames.get(key, {}))
        if strokes is not None:
            if strokes:
                entry["strokes"] = [s.to_dict() for s in strokes]
            else:
                entry.pop("strokes", None)
        if note is not None:
            if note:
                entry["note"] = note
            else:
                entry.pop("note", None)
        if entry:
            frames[key] = entry
        else:
            frames.pop(key, None)
        comment_store.save(self._video_path, frames)

    # -- toolbar ----------------------------------------------------------

    def _on_pick_color(self) -> None:
        color = QColorDialog.getColor(self._current_color, self, "Pen Color")
        if color.isValid():
            self._current_color = color
            self.draw_overlay.set_color(color)
            self._update_color_button()

    def _update_color_button(self) -> None:
        self.color_button.setStyleSheet(f"background-color: {self._current_color.name()};")
