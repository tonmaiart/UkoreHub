from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.git_service import GitService
from core.github.commits_api import GitHubCommitsApiError, download_bytes, fetch_commits_for_path
from interface.shared.widget_helpers import wrap_scrollable

AVATAR_SIZE = 22


@dataclass
class CommitHistoryEntry:
    hash: str
    author_display: str
    date: str
    message: str
    avatar_bytes: bytes | None


def format_commit_date(raw: str) -> str:
    """Best-effort "15 Jan 2024" from git's ISO (%aI) or GitHub API's
    ISO-with-Z date strings. Falls back to the raw string if it can't be
    parsed, rather than raising — a display nicety is never worth crashing
    the commit history over."""
    if not raw:
        return raw
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return raw
    return dt.strftime("%d %b %Y")


def fetch_entries_via_github(
    git_service: GitService,
    repo_path: Path,
    relative_path: str,
    token: str | None,
    limit: int,
    page: int,
    avatar_cache: dict[str, bytes | None],
) -> list[CommitHistoryEntry] | None:
    """Returns None (never an empty list) when the repo has no github.com
    origin or the API call fails, so callers know to fall back to local git
    instead of showing a false "no commits" result."""
    owner_repo = git_service.get_github_owner_repo(repo_path)
    if owner_repo is None:
        return None
    owner, repo = owner_repo
    try:
        raw_commits = fetch_commits_for_path(owner, repo, relative_path, token, limit, page=page)
    except GitHubCommitsApiError:
        return None

    entries = []
    for item in raw_commits:
        commit_info = item.get("commit", {}) or {}
        author_info = commit_info.get("author", {}) or {}
        gh_author = item.get("author")
        if gh_author:
            display_name = gh_author.get("login") or author_info.get("name", "unknown")
            avatar_url = gh_author.get("avatar_url")
        else:
            display_name = author_info.get("name", "unknown")
            avatar_url = None

        avatar_bytes = None
        if avatar_url:
            if avatar_url not in avatar_cache:
                avatar_cache[avatar_url] = download_bytes(avatar_url)
            avatar_bytes = avatar_cache[avatar_url]

        entries.append(
            CommitHistoryEntry(
                hash=(item.get("sha") or "")[:10],
                author_display=display_name,
                date=author_info.get("date", ""),
                message=commit_info.get("message", ""),
                avatar_bytes=avatar_bytes,
            )
        )
    return entries


class CommitCard(QFrame):
    """Shared visual template for a single commit: avatar (or a generic
    person glyph when none is available), author + human-readable date,
    and message. Used by both the Explorer tab's per-path commit history
    panel and the Submit tab's whole-repo commit log.

    Passing git_service + repo_path makes the card expandable — a "Files"
    button pops open a separate window listing the files changed in that
    commit, each with its own "Browse" button that hands the resolved
    absolute path to on_browse_file (Submit tab wires this to jump to the
    Explorer tab). Without them (the Explorer tab's per-path panel), the
    card is plain."""

    def __init__(
        self,
        entry: CommitHistoryEntry,
        parent=None,
        *,
        git_service: GitService | None = None,
        repo_path: Path | None = None,
        on_browse_file: Callable[[Path], None] | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("commitCard")
        self.setFrameShape(QFrame.StyledPanel)
        self._entry = entry
        self._git_service = git_service
        self._repo_path = repo_path
        self._on_browse_file = on_browse_file
        self._files_dialog: _CommitFilesDialog | None = None
        self._expandable = git_service is not None and repo_path is not None

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

        header_label = QLabel(f"<b>{entry.author_display}</b>  ·  {format_commit_date(entry.date)}")
        header_label.setWordWrap(True)
        message_label = QLabel(entry.message)
        message_label.setWordWrap(True)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)
        text_layout.addWidget(header_label)
        text_layout.addWidget(message_label)

        top_row = QHBoxLayout()
        top_row.setSpacing(4)
        top_row.addWidget(avatar_label, alignment=Qt.AlignTop)
        top_row.addLayout(text_layout, stretch=1)

        if self._expandable:
            files_button = QPushButton("Files")
            files_button.setFixedWidth(50)
            files_button.clicked.connect(self._on_files_clicked)
            top_row.addWidget(files_button, alignment=Qt.AlignTop)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(4, 3, 4, 3)
        outer_layout.addLayout(top_row)

    def _on_files_clicked(self) -> None:
        # Non-modal, like browser_widget.py's opening popup — a fresh dialog
        # per click, replacing the previous one (if the user clicked Files
        # again while it was already open) rather than stacking windows.
        if self._files_dialog is not None:
            self._files_dialog.close()
        self._files_dialog = _CommitFilesDialog(
            self,
            git_service=self._git_service,
            repo_path=self._repo_path,
            entry=self._entry,
            on_browse_file=self._on_browse_file,
        )
        self._files_dialog.show()


class _CommitFilesDialog(QDialog):
    """Popup window listing the files changed in one commit — replaces the
    old inline-expanding "Files" row so the commit list itself doesn't grow
    taller as you inspect commits. Non-modal so "Browse" (which jumps to the
    Explorer tab) doesn't force closing this window first."""

    def __init__(
        self,
        parent,
        *,
        git_service: GitService,
        repo_path: Path,
        entry: CommitHistoryEntry,
        on_browse_file: Callable[[Path], None] | None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Files Changed — {entry.hash}")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.resize(420, 320)
        self._repo_path = repo_path
        self._on_browse_file = on_browse_file

        files = git_service.get_commit_files(repo_path, entry.hash)
        content = QWidget()
        files_layout = QVBoxLayout(content)
        if not files:
            files_layout.addWidget(QLabel("No file changes recorded."))
        for relative_path in files:
            row = QHBoxLayout()
            row.addWidget(QLabel(relative_path), stretch=1)
            browse_button = QPushButton("Browse")
            browse_button.setFixedWidth(70)
            browse_button.clicked.connect(lambda _checked, p=relative_path: self._browse_to(p))
            row.addWidget(browse_button)
            files_layout.addLayout(row)
        files_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(wrap_scrollable(content))

    def _browse_to(self, relative_path: str) -> None:
        if self._on_browse_file is not None:
            self._on_browse_file(Path(self._repo_path) / relative_path)
