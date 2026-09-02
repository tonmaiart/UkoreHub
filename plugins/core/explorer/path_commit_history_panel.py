from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from plugin_api import CommitHistoryEntry, GitService, avatar_table_icon, format_commit_date
from plugins.core.explorer.path_commit_history_worker import PathCommitHistoryWorker

_COLUMN_LABELS = ("Author", "Message", "Time")
_MESSAGE_COLUMN = 1


class PathCommitHistoryPanel:
    """Commit history scoped to whichever path is currently being viewed in
    the Repo Browser — narrower than the whole-repo log on Repo Git Status.
    Renders into `tableWidget_file_commit_history` (authored directly in
    explorer_section.ui) rather than owning its own widget tree."""

    def __init__(self, git_service: GitService, table: QTableWidget):
        self.git_service = git_service
        self.table = table
        self._worker: PathCommitHistoryWorker | None = None

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
        # Workers being replaced before their own run() has fully unwound on
        # the OS thread — see _retire_worker below.
        self._retiring_workers: set[PathCommitHistoryWorker] = set()

        self.table.setColumnCount(len(_COLUMN_LABELS))
        self.table.setHorizontalHeaderLabels(_COLUMN_LABELS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(_MESSAGE_COLUMN, QHeaderView.Stretch)

        self.clear()

    def clear(self) -> None:
        """No file selected (folder navigation, cleared selection, or a
        directory row) — reset to empty instead of leaving the
        previously-selected file's history on screen."""
        self._current_key = None
        self.table.clearSpans()
        self.table.setRowCount(0)

    def show_commits_for(self, repo_path: Path, relative_path: str) -> None:
        cache_key = (str(repo_path), relative_path)
        self._current_key = cache_key
        cached = self._entries_cache.get(cache_key)
        if cached is not None:
            self._render_entries(cached)
        else:
            self._show_message_row("Loading...")

        if self._worker is not None and self._worker.isRunning():
            self._pending_request = (repo_path, relative_path)
            return
        self._pending_request = None
        self._start_fetch(repo_path, relative_path, cache_key)

    def _start_fetch(self, repo_path: Path, relative_path: str, cache_key: tuple[str, str]) -> None:
        if self._worker is not None:
            self._retire_worker(self._worker)

        token = self.git_service.get_github_token()
        self._worker = PathCommitHistoryWorker(
            self.git_service, repo_path, relative_path, token, avatar_cache=self._avatar_cache
        )
        self._worker.entries_ready.connect(lambda entries: self._on_entries_ready(entries, cache_key))
        self._worker.start()

    def _retire_worker(self, worker: PathCommitHistoryWorker) -> None:
        # Reassigning self._worker must never drop the last Python reference
        # to a QThread before it has actually finished. entries_ready is
        # emitted as the very last line of run(), so _on_entries_ready can
        # turn around and call _start_fetch again (for a queued pending
        # request) while the old worker's OS thread is still unwinding —
        # PySide6 destroys the underlying QThread the instant its Python
        # refcount hits zero, and doing that before the thread has fully
        # stopped is a documented Qt crash ("QThread: Destroyed while thread
        # is still running"), one that gets far more likely the faster
        # _start_fetch is called back-to-back, i.e. exactly when the user
        # double-clicks through folders quickly. Keeping a strong reference
        # around until finished() actually fires avoids that race entirely.
        if worker.isFinished():
            return
        self._retiring_workers.add(worker)
        worker.finished.connect(lambda: self._retiring_workers.discard(worker))

    def _show_message_row(self, message: str) -> None:
        self.table.clearSpans()
        self.table.setRowCount(1)
        item = QTableWidgetItem(message)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(0, 0, item)
        self.table.setSpan(0, 0, 1, len(_COLUMN_LABELS))

    def _render_entries(self, entries: list[CommitHistoryEntry]) -> None:
        self.table.clearSpans()
        if not entries:
            self._show_message_row("No commit history found.")
            return

        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            author_item = QTableWidgetItem(entry.author_display)
            icon = avatar_table_icon(entry.avatar_bytes)
            if icon:
                author_item.setIcon(icon)

            message_item = QTableWidgetItem(entry.message)
            message_item.setToolTip(entry.message)

            time_item = QTableWidgetItem(format_commit_date(entry.date))

            for item in (author_item, message_item, time_item):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(row, 0, author_item)
            self.table.setItem(row, 1, message_item)
            self.table.setItem(row, 2, time_item)

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
