from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.git_service import GitService
from interface.commit_history import CommitHistoryEntry, fetch_entries_via_github


class CommitLogWorker(QThread):
    log_ready = Signal(list)

    def __init__(
        self,
        git_service: GitService,
        repo_path: Path,
        skip: int,
        limit: int,
        github_token: str | None = None,
        avatar_cache: dict[str, bytes | None] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.git_service = git_service
        self.repo_path = repo_path
        self.skip = skip
        self.limit = limit
        self.github_token = github_token
        # Shared across every "Load More" click and repo switch in a
        # session, so an author's avatar is only ever downloaded once.
        self._avatar_cache = avatar_cache if avatar_cache is not None else {}

    def run(self) -> None:
        entries = None
        if self.limit > 0:
            # GitHub's commits API paginates by page number, not skip/offset;
            # skip only ever advances by whole page-sized chunks in this
            # app's usage (see repo_git_status_page.py), so this mapping is
            # exact except at the very tail of history — an acceptable
            # trade-off for a "Load More" convenience button.
            page = self.skip // self.limit + 1
            entries = fetch_entries_via_github(
                self.git_service, self.repo_path, "", self.github_token, self.limit, page, self._avatar_cache
            )
        if entries is None:
            commits = self.git_service.get_commit_log(self.repo_path, skip=self.skip, limit=self.limit)
            entries = [
                CommitHistoryEntry(
                    hash=commit.hash[:10],
                    author_display=commit.author,
                    date=commit.date,
                    message=commit.message,
                    avatar_bytes=None,
                )
                for commit in commits
            ]
        self.log_ready.emit(entries)
