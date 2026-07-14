from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.git_service import GitService
from interface.explorer.path_commit_history_worker import PathCommitHistoryWorker
from interface.shared.commit_history import CommitCard, CommitHistoryEntry
from interface.shared.widget_helpers import wrap_scrollable


class PathCommitHistoryPanel(QWidget):
    """Commit history scoped to whichever path is currently being viewed in
    the Repo Browser — narrower than the whole-repo log on Repo Git Status."""

    def __init__(self, git_service: GitService, parent=None):
        super().__init__(parent)
        self.git_service = git_service
        self._worker: PathCommitHistoryWorker | None = None
        self.setFixedWidth(230)

        # Session-lifetime caches so re-visiting a file/folder you've already
        # clicked shows instantly instead of re-running git/GitHub every time.
        # Keyed by (repo_path, relative_path) since the same relative path can
        # exist in more than one repo.
        self._entries_cache: dict[tuple[str, str], list[CommitHistoryEntry]] = {}
        self._avatar_cache: dict[str, bytes | None] = {}
        self._current_key: tuple[str, str] | None = None
        # If the user clicks another file while a fetch is still running, the
        # old code silently dropped the new click. Remember it here and fire
        # it as soon as the in-flight worker finishes instead of losing it.
        self._pending_request: tuple[Path, str] | None = None

        title = QLabel("Commit History")
        title.setObjectName("commitHistoryTitle")

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.addStretch()

        scroll = wrap_scrollable(self._cards_container, object_name="commitHistoryScroll")

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self._status_label)
        layout.addWidget(scroll, stretch=1)

    def show_commits_for(self, repo_path: Path, relative_path: str) -> None:
        cache_key = (str(repo_path), relative_path)
        self._current_key = cache_key
        cached = self._entries_cache.get(cache_key)
        if cached is not None:
            self._render_entries(cached)
        else:
            self._clear_cards()
            self._status_label.setText("Loading...")

        if self._worker is not None and self._worker.isRunning():
            self._pending_request = (repo_path, relative_path)
            return
        self._pending_request = None
        self._start_fetch(repo_path, relative_path, cache_key)

    def _start_fetch(self, repo_path: Path, relative_path: str, cache_key: tuple[str, str]) -> None:
        token = self.git_service.get_github_token()
        self._worker = PathCommitHistoryWorker(
            self.git_service, repo_path, relative_path, token, avatar_cache=self._avatar_cache
        )
        self._worker.entries_ready.connect(lambda entries: self._on_entries_ready(entries, cache_key))
        self._worker.start()

    def _clear_cards(self) -> None:
        while self._cards_layout.count() > 1:  # keep the trailing stretch
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_entries(self, entries: list) -> None:
        self._clear_cards()
        self._status_label.setText("No commit history found." if not entries else "")
        for entry in entries:
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, CommitCard(entry))

    def _on_entries_ready(self, entries: list, cache_key: tuple[str, str]) -> None:
        self._entries_cache[cache_key] = entries
        # Only repaint if the user hasn't already navigated to something else
        # while this fetch was running — avoids flashing stale results over
        # whatever they're currently looking at.
        if cache_key == self._current_key:
            self._render_entries(entries)

        if self._pending_request is not None:
            repo_path, relative_path = self._pending_request
            self._pending_request = None
            self._start_fetch(repo_path, relative_path, (str(repo_path), relative_path))
