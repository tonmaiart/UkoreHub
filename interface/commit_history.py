from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from core.git_service import GitService
from core.github.commits_api import GitHubCommitsApiError, download_bytes, fetch_commits_for_path

AVATAR_SIZE = 32


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
    panel and the Submit tab's whole-repo commit log."""

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

        header_label = QLabel(f"<b>{entry.author_display}</b>  ·  {format_commit_date(entry.date)}")
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
