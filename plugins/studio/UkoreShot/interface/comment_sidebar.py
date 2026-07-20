from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

_WIDTH = 64


class CommentSidebar(QListWidget):
    """Right-hand sidebar — used by PlayerWidget in both show_edit_tools
    modes — listing every frame with a saved comment, top-to-bottom by
    frame index. A plain QListWidget matching
    interface/settings/settings_view.py's SettingsView.tab_list style
    (fixed-width, flat rows, click-or-drag-through to select) rather than
    a card grid — the user's own 2026-07-20 request. Each row is just the
    frame number, no "Frame" label. currentRowChanged (not itemClicked)
    is what drives frameSelected, so pressing on one row and dragging
    across others scrubs through commented frames live, the same native
    QListWidget click-drag-select behavior Settings' tab_list gets for
    free."""

    frameSelected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(_WIDTH)
        self._suppress_selection_signal = False
        self.currentRowChanged.connect(self._on_row_changed)

    def set_frames(self, frames: dict) -> None:
        """frames is PlayerWidget._frames["frames"] — {"<index>": {...}}.
        Rebuilds every row from scratch — called whenever the underlying
        comment data changes (video load/clear, a stroke/note/text box
        saved), not on every frame navigation."""
        self._suppress_selection_signal = True
        self.clear()
        indices = sorted(int(key) for key, entry in frames.items() if entry)
        for index in indices:
            item = QListWidgetItem(str(index))
            item.setData(Qt.UserRole, index)
            item.setTextAlignment(Qt.AlignCenter)
            self.addItem(item)
        self._suppress_selection_signal = False

    def set_current_frame(self, frame_index: int) -> None:
        """Highlights whichever row matches the frame currently playing,
        without emitting frameSelected — that signal is only for the user
        actively picking a row, not PlayerWidget echoing its own state
        back in."""
        self._suppress_selection_signal = True
        for row in range(self.count()):
            if self.item(row).data(Qt.UserRole) == frame_index:
                self.setCurrentRow(row)
                self._suppress_selection_signal = False
                return
        self.setCurrentRow(-1)
        self._suppress_selection_signal = False

    def _on_row_changed(self, row: int) -> None:
        if self._suppress_selection_signal or row < 0:
            return
        item = self.item(row)
        if item is not None:
            self.frameSelected.emit(item.data(Qt.UserRole))
