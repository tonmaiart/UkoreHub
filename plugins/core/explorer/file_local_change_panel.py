from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from plugin_api import FileChange, GitService, LocalConfigStore
from plugins.core.explorer.file_local_change_worker import FileLocalChangeWorker
from plugins.core.explorer.file_table_proxy import format_time_ago

_COLUMN_LABELS = ("Author", "Time")


class FileLocalChangePanel:
    """Whether the currently-selected file has an uncommitted local change —
    renders into tableWidget_file_local_change (explorer_section.ui). Only
    ever populated for an actual file selection (see
    RepoBrowserWidget._on_table_selection_changed); folder navigation clears
    it via clear()."""

    def __init__(self, git_service: GitService, table: QTableWidget, local_config_store: LocalConfigStore | None):
        self.git_service = git_service
        self.table = table
        self._local_config_store = local_config_store
        self._worker: FileLocalChangeWorker | None = None
        # See PathCommitHistoryPanel._retire_worker for why this is needed —
        # same QThread-lifetime hazard applies here.
        self._retiring_workers: set[FileLocalChangeWorker] = set()
        self._current_key: tuple[str, str] | None = None

        self.table.setColumnCount(len(_COLUMN_LABELS))
        self.table.setHorizontalHeaderLabels(_COLUMN_LABELS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        self.clear()

    def show_local_change_for(self, repo_path: Path, relative_path: str) -> None:
        cache_key = (str(repo_path), relative_path)
        self._current_key = cache_key
        self._show_message_row("Checking...")

        if self._worker is not None:
            self._retire_worker(self._worker)

        worker = FileLocalChangeWorker(self.git_service, repo_path, relative_path)
        worker.result_ready.connect(lambda result: self._on_result_ready(result, cache_key))
        self._worker = worker
        worker.start()

    def clear(self) -> None:
        """No file selected (folder navigation, cleared selection, or a
        directory row) — nothing to look up, so just reset to empty instead
        of leaving the previous file's row on screen."""
        self._current_key = None
        self.table.clearSpans()
        self.table.setRowCount(0)

    def _retire_worker(self, worker: FileLocalChangeWorker) -> None:
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

    def _on_result_ready(self, result, cache_key: tuple[str, str]) -> None:
        if cache_key != self._current_key:
            return
        change, mtime = result
        change: FileChange | None
        if change is None:
            self._show_message_row("No local change.")
            return

        author = None
        if self._local_config_store is not None:
            author = getattr(self._local_config_store, "github_username", None)

        self.table.clearSpans()
        self.table.setRowCount(1)
        author_item = QTableWidgetItem(author or "You")
        time_item = QTableWidgetItem(format_time_ago(mtime) if mtime is not None else "")
        for item in (author_item, time_item):
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(0, 0, author_item)
        self.table.setItem(0, 1, time_item)
