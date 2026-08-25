from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QIcon, QPixmap

from plugin_api import GitOperationError, GitService, fetch_avatar_bytes, fetch_entries_via_github


@dataclass
class FileAuthorInfo:
    local_modified_by: str | None = None
    local_modified_icon: QIcon | None = None
    last_commit_by: str | None = None
    last_commit_icon: QIcon | None = None


class FileRowAuthorsWorker(QThread):
    """For every entry (file or folder) in the currently-open folder,
    resolves "Local Modified By" (one git status call for the whole folder,
    reused for every entry — the signed-in user, since an uncommitted
    change has no commit author) and "Last Commit By" (GitHub-API-first,
    local-git-fallback, one lookup per entry — same pattern as
    PathCommitHistoryWorker). Emits progressively, one entry at a time, so
    rows fill in as results arrive instead of the whole column staying
    blank until every entry in the folder is done.

    last_commit_cache is a dict owned by RepoBrowserWidget and shared
    across every FileRowAuthorsWorker instance over the widget's lifetime —
    "last commit by" for a given relative_path doesn't change without a new
    commit landing, so it's fetched once and reused on every later
    revisit rather than re-querying git/GitHub every navigation. Safe to
    mutate directly from run() (background thread) because, like
    PathCommitHistoryPanel's avatar_cache, only one worker is ever active
    at a time (RepoBrowserWidget retires the previous one before starting
    a new one) and the GUI thread never touches this dict itself, only the
    per-entry results delivered via entry_ready.

    Checks isInterruptionRequested() between entries so navigating away
    mid-fetch stops promptly without killing a git/network call
    mid-flight."""

    entry_ready = Signal(str, object)  # abs_path, FileAuthorInfo

    def __init__(
        self,
        git_service: GitService,
        repo_path: Path,
        entries: list[tuple[str, str, bool]],  # (abs_path, relative_path, is_dir)
        github_username: str | None,
        github_token: str | None,
        last_commit_cache: dict[str, tuple[str | None, QIcon | None]],
        parent=None,
    ):
        super().__init__(parent)
        self.git_service = git_service
        self.repo_path = repo_path
        self.entries = entries
        self.github_username = github_username
        self.github_token = github_token
        self.last_commit_cache = last_commit_cache
        self._avatar_bytes_cache: dict[str, bytes | None] = {}

    def run(self) -> None:
        locally_modified = self._get_locally_modified_paths()
        my_icon = self._current_user_icon()

        for abs_path, relative_path, is_dir in self.entries:
            if self.isInterruptionRequested():
                return

            info = FileAuthorInfo()
            if not is_dir and relative_path in locally_modified:
                info.local_modified_by = self.github_username or "You"
                info.local_modified_icon = my_icon

            cached = self.last_commit_cache.get(relative_path)
            if cached is None:
                cached = self._fetch_last_commit_author(relative_path)
                self.last_commit_cache[relative_path] = cached
            info.last_commit_by, info.last_commit_icon = cached

            self.entry_ready.emit(abs_path, info)

    def _get_locally_modified_paths(self) -> set[str]:
        try:
            status = self.git_service.get_status(self.repo_path)
        except GitOperationError:
            return set()
        return {change.path for change in (*status.unstaged_changes, *status.staged_changes)}

    def _current_user_icon(self) -> QIcon | None:
        if not self.github_username:
            return None
        avatar_bytes = fetch_avatar_bytes(self.github_username)
        return self._icon_from_bytes(avatar_bytes)

    def _fetch_last_commit_author(self, relative_path: str) -> tuple[str | None, QIcon | None]:
        entries = fetch_entries_via_github(
            self.git_service, self.repo_path, relative_path, self.github_token, 1, 1, self._avatar_bytes_cache
        )
        if entries is None:
            try:
                commits = self.git_service.get_commit_log_for_path(self.repo_path, relative_path, 1)
            except GitOperationError:
                commits = []
            if not commits:
                return None, None
            return commits[0].author, None

        if not entries:
            return None, None
        entry = entries[0]
        return entry.author_display, self._icon_from_bytes(entry.avatar_bytes)

    @staticmethod
    def _icon_from_bytes(avatar_bytes: bytes | None) -> QIcon | None:
        if not avatar_bytes:
            return None
        pixmap = QPixmap()
        pixmap.loadFromData(avatar_bytes)
        if pixmap.isNull():
            return None
        return QIcon(pixmap)
