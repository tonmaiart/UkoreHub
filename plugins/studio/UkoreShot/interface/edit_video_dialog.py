from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialog, QVBoxLayout

from plugins.studio.UkoreShot.interface.player_widget import PlayerWidget


class EditVideoDialog(QDialog):
    """Popped up by the library page's "Edit Comment" button — the actual
    frame-by-frame comment/grease-pencil editor, kept out of the inline
    library view so just watching a video doesn't always show the draw
    toolbar and comment box. Wraps a single edit-mode PlayerWidget; all
    persistence (comment_store) happens through it exactly as before."""

    def __init__(self, video_path: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Video - {video_path.name}")
        self.resize(900, 700)

        self.player_widget = PlayerWidget(show_edit_tools=True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.player_widget)

        self.player_widget.load_video(video_path)
