from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.git_service import GitService
from interface.commit_history import CommitHistoryEntry, fetch_entries_via_github


class PathCommitHistoryWorker(QThread):
    entries_ready = Signal(list)

    def __init__(
        self,
        git_service: GitService,
        repo_path: Path,
        relative_path: str,
        github_token: str | None,
        limit: int = 30,
        avatar_cache: dict[str, bytes | None] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.git_service = git_service
        self.repo_path = repo_path
        self.relative_path = relative_path
        self.github_token = github_token
        self.limit = limit
        # Shared across every path the user clicks through in a session, so an
        # author's avatar is only ever downloaded once instead of on every
        # single file/folder click — this is the slow part of each fetch.
        self._avatar_cache = avatar_cache if avatar_cache is not None else {}

    def run(self) -> None:
        entries = fetch_entries_via_github(
            self.git_service, self.repo_path, self.relative_path, self.github_token, self.limit, 1, self._avatar_cache
        )
        if entries is None:
            entries = self._fetch_via_local_git()
        self.entries_ready.emit(entries)

    def _fetch_via_local_git(self) -> list[CommitHistoryEntry]:
        commits = self.git_service.get_commit_log_for_path(self.repo_path, self.relative_path, self.limit)
        return [
            CommitHistoryEntry(
                hash=commit.hash[:10],
                author_display=commit.author,
                date=commit.date,
                message=commit.message,
                avatar_bytes=None,
            )
            for commit in commits
        ]
