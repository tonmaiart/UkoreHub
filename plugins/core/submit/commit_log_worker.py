from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from plugin_api import CommitHistoryEntry, GitOperationError, GitService, fetch_entries_via_github

_FETCH_LIMIT = 20


class CommitLogWorker(QThread):
    """Background fetch for Submit's two commit-history panels —
    tableView_local_commit_history (this machine's own local git log, i.e.
    HEAD) and tableView_new_commit_history (commits already on origin's
    tracking branch that this clone hasn't pulled in yet — what "Sync New
    Commit" would bring in, i.e. teammates' unsynced work). A best-effort
    `git fetch` (remote-tracking refs only, never the working tree — see
    GitService.fetch) runs first so the "new" list can see commits nobody
    has pulled into this clone yet. Both lists are built purely from local
    git — no GitHub API call there, since the "new" list needs a
    HEAD..origin/<branch> revision range the GitHub commits feed has no way
    to express — but avatars are still backfilled from a single GitHub API
    "recent commits" call afterward (best-effort, matched by commit hash),
    so this still shows real avatars for anything GitHub knows about
    instead of always falling back to the generic glyph."""

    entries_ready = Signal(list, list)  # local_entries, new_entries

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
        # instead of on every 30-minute repoll.
        self._avatar_cache = avatar_cache if avatar_cache is not None else {}

    def run(self) -> None:
        try:
            self.git_service.fetch(self.repo_path)
        except GitOperationError:
            pass  # offline/auth hiccup — fall back to whatever's already local

        local_entries = self._entries_for_ref(None)

        new_entries: list[CommitHistoryEntry] = []
        try:
            branch = self.git_service.get_current_branch(self.repo_path)
            new_entries = self._entries_for_ref(f"HEAD..origin/{branch}")
        except GitOperationError:
            pass  # no branch/upstream yet — nothing "new" to report

        self._backfill_avatars(local_entries, new_entries)
        self.entries_ready.emit(local_entries, new_entries)

    def _entries_for_ref(self, ref: str | None) -> list[CommitHistoryEntry]:
        kwargs = {"limit": _FETCH_LIMIT}
        if ref is not None:
            kwargs["ref"] = ref
        commits = self.git_service.get_commit_log(self.repo_path, **kwargs)
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

    def _backfill_avatars(
        self, local_entries: list[CommitHistoryEntry], new_entries: list[CommitHistoryEntry]
    ) -> None:
        """Best-effort: matches local-git entries (hash, no avatar) against
        GitHub's own recent-commits feed (hash + avatar) by commit hash, and
        copies the avatar over where they match. Silently leaves the 👤
        fallback glyph in place for anything GitHub's feed doesn't cover
        (not a github.com remote, offline, rate-limited, or a commit old
        enough to have fallen off the fetched page) — this is a display
        nicety, never worth failing the panel over."""
        api_entries = fetch_entries_via_github(
            self.git_service, self.repo_path, "", self.github_token, _FETCH_LIMIT, 1, self._avatar_cache
        )
        if not api_entries:
            return
        avatar_by_hash = {entry.hash: entry.avatar_bytes for entry in api_entries if entry.avatar_bytes}
        for entry in [*local_entries, *new_entries]:
            avatar = avatar_by_hash.get(entry.hash)
            if avatar:
                entry.avatar_bytes = avatar
