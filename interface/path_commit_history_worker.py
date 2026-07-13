from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.git_service import GitService
from core.github.commits_api import GitHubCommitsApiError, download_bytes, fetch_commits_for_path


@dataclass
class CommitHistoryEntry:
    hash: str
    author_display: str
    date: str
    message: str
    avatar_bytes: bytes | None


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
        entries = self._fetch_via_github_api()
        if entries is None:
            entries = self._fetch_via_local_git()
        self.entries_ready.emit(entries)

    def _fetch_via_github_api(self) -> list[CommitHistoryEntry] | None:
        owner_repo = self.git_service.get_github_owner_repo(self.repo_path)
        if owner_repo is None:
            return None
        owner, repo = owner_repo
        try:
            raw_commits = fetch_commits_for_path(owner, repo, self.relative_path, self.github_token, self.limit)
        except GitHubCommitsApiError:
            return None

        avatar_cache = self._avatar_cache
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
