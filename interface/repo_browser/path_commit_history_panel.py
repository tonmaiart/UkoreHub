from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.git_service import GitService
from interface.path_commit_history_worker import CommitHistoryEntry, PathCommitHistoryWorker

AVATAR_SIZE = 32


class CommitCard(QFrame):
    def __init__(self, entry: CommitHistoryEntry, parent=None):
        super().__init__(parent)
        self.setObjectName("commitCard")
        self.setFrameShape(QFrame.StyledPanel)

        avatar_label = QLabel()
        avatar_label.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        if entry.avatar_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(entry.avatar_bytes)
            avatar_label.setPixmap(
                pixmap.scaled(AVATAR_SIZE, AVATAR_SIZE, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            )
        else:
            avatar_label.setText("\U0001F464")
            avatar_label.setAlignment(Qt.AlignCenter)

        header_label = QLabel(f"<b>{entry.author_display}</b>  ·  {entry.date}")
        header_label.setWordWrap(True)
        message_label = QLabel(entry.message)
        message_label.setWordWrap(True)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.addWidget(header_label)
        text_layout.addWidget(message_label)

        row_layout = QHBoxLayout(self)
        row_layout.addWidget(avatar_label, alignment=Qt.AlignTop)
        row_layout.addLayout(text_layout, stretch=1)


class PathCommitHistoryPanel(QWidget):
    """Commit history scoped to whichever path is currently being viewed in
    the Repo Browser — narrower than the whole-repo log on Repo Git Status."""

    def __init__(self, git_service: GitService, parent=None):
        super().__init__(parent)
        self.git_service = git_service
        self._worker: PathCommitHistoryWorker | None = None
        self.setFixedWidth(260)

        title = QLabel("Commit History")

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(self._cards_container)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self._status_label)
        layout.addWidget(scroll)

    def show_commits_for(self, repo_path: Path, relative_path: str) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        self._clear_cards()
        self._status_label.setText("Loading...")
        token = self.git_service.get_github_token()
        self._worker = PathCommitHistoryWorker(self.git_service, repo_path, relative_path, token)
        self._worker.entries_ready.connect(self._on_entries_ready)
        self._worker.start()

    def _clear_cards(self) -> None:
        while self._cards_layout.count() > 1:  # keep the trailing stretch
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _on_entries_ready(self, entries: list) -> None:
        self._clear_cards()
        self._status_label.setText("No commit history found." if not entries else "")
        for entry in entries:
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, CommitCard(entry))
