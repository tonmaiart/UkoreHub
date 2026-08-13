from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from plugin_api import CommitHistoryEntry, GitOperationError, GitService, fetch_entries_via_github

_FETCH_LIMIT = 20


class CommitLogWorker(QThread):
    """Background fetch for Submit's whole-repo commit history panel —
    refetches the active repo's most recent commits (GitHub-API-first,
    local-git-fallback, same approach interface/shared/commit_history.py's
    other callers use) so commits pushed by teammates from their own
    machines show up too, not just this machine's own pushes. A best-effort
    `git fetch` (remote-tracking refs only, never the working tree — see
    GitService.fetch) runs first so the local fallback path can see commits
    nobody has pulled into this clone yet."""

    entries_ready = Signal(list)

    def __init__(
        self,
        git_service: GitService,
        repo_path: Path,
        github_token: str | None,
        avatar_cache: dict[str, bytes | None] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.git_service = git_service
        self.repo_path = repo_path
        self.github_token = github_token
        # Shared across every poll (page keeps this alive for the page's own
        # lifetime), so an author's avatar is only ever downloaded once
        # instead of on every 30-minute repoll — same idiom
        # PathCommitHistoryWorker uses for Explorer's panel.
        self._avatar_cache = avatar_cache if avatar_cache is not None else {}

    def run(self) -> None:
        try:
            self.git_service.fetch(self.repo_path)
        except GitOperationError:
            pass  # offline/auth hiccup — fall back to whatever's already local

        entries = fetch_entries_via_github(
            self.git_service, self.repo_path, "", self.github_token, _FETCH_LIMIT, 1, self._avatar_cache
        )
        if entries is None:
            commits = []
            try:
                branch = self.git_service.get_current_branch(self.repo_path)
                commits = self.git_service.get_commit_log(self.repo_path, limit=_FETCH_LIMIT, ref=f"origin/{branch}")
            except GitOperationError:
                pass
            if not commits:
                # No matching remote-tracking branch (fetch failed/never ran,
                # or this branch isn't pushed yet) — fall back to local HEAD,
                # same as Explorer's per-path panel, instead of showing
                # nothing even though local history exists.
                commits = self.git_service.get_commit_log(self.repo_path, limit=_FETCH_LIMIT)
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
        self.entries_ready.emit(entries)
