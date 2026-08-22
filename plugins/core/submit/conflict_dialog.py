from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFile, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plugin_api import GitService, fetch_avatar_bytes, fetch_entries_via_github
from plugins.core.submit.git_stream_worker import GitStreamWorker

_UI_FILE = Path(__file__).resolve().parent / "MergeConflictResolveWindow.ui"
_AVATAR_SIZE = 22
_FALLBACK_GLYPH = "\U0001F464"

# tableWidget_conflict_info columns.
_COL_FILE = 0
_COL_MY_AVATAR = 1
_COL_MY_USERNAME = 2
_COL_MY_STATUS = 3
_COL_OTHER_AVATAR = 4
_COL_OTHER_USERNAME = 5
_COL_OTHER_STATUS = 6


def _load_ui_form(parent: QWidget | None = None) -> QWidget:
    """Loads MergeConflictResolveWindow.ui at runtime (QUiLoader, no compile
    step), same idiom as submit_section.ui's own _load_ui_form."""
    loader = QUiLoader()
    ui_file = QFile(str(_UI_FILE))
    ui_file.open(QFile.ReadOnly)
    try:
        form = loader.load(ui_file, parent)
    finally:
        ui_file.close()
    return form


def _avatar_item(avatar_bytes: bytes | None) -> QTableWidgetItem:
    item = QTableWidgetItem()
    if avatar_bytes:
        pixmap = QPixmap()
        pixmap.loadFromData(avatar_bytes)
        item.setIcon(QIcon(pixmap))
    else:
        item.setText(_FALLBACK_GLYPH)
        item.setTextAlignment(Qt.AlignCenter)
    return item


class ConflictResolutionDialog(QDialog):
    """Per-file (not per-line) merge conflict resolution — appropriate for a
    mostly-binary animation production pipeline where line-level diffing
    doesn't make sense. Loads MergeConflictResolveWindow.ui's
    tableWidget_conflict_info, one row per conflicted file, showing both
    sides' identity (avatar + username) so it's clear whose change is whose
    before picking Choose Mine/Choose Other. Multi-selection: both buttons
    act on every selected row at once, not just the current row."""

    def __init__(
        self,
        parent=None,
        *,
        git_service: GitService,
        repo_path: Path,
        github_token: str | None,
        my_username: str,
        conflicted_files: list[str],
    ):
        super().__init__(parent)
        self.setWindowTitle("Resolve Merge Conflicts")
        self.git_service = git_service
        self.repo_path = repo_path
        self.github_token = github_token
        self.my_username = my_username or "You"
        self.conflicted_files = conflicted_files
        self._resolutions: dict[str, str] = {}
        self._other_avatar_cache: dict[str, bytes | None] = {}
        self._author_worker: GitStreamWorker | None = None

        self._ui = _load_ui_form(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)
        self.resize(self._ui.size())

        self.table: QTableWidget = self._ui.findChild(QTableWidget, "tableWidget_conflict_info")
        self.choose_mine_button: QPushButton = self._ui.findChild(QPushButton, "pushButton_choose_mine")
        self.choose_other_button: QPushButton = self._ui.findChild(QPushButton, "pushButton_choose_other")
        self.cancel_button: QPushButton = self._ui.findChild(QPushButton, "pushButton_cancel")
        self.resolve_button: QPushButton = self._ui.findChild(QPushButton, "pushButton_resolve_and_sync")

        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["File", "", "My Username", "Status", "", "Other Username", "Status"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setIconSize(QSize(_AVATAR_SIZE, _AVATAR_SIZE))
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(_COL_FILE, QHeaderView.Stretch)
        for col in (_COL_MY_AVATAR, _COL_MY_STATUS, _COL_OTHER_AVATAR, _COL_OTHER_STATUS):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.choose_mine_button.clicked.connect(lambda: self._apply_choice("ours"))
        self.choose_other_button.clicked.connect(lambda: self._apply_choice("theirs"))
        self.cancel_button.clicked.connect(self.reject)
        self.resolve_button.clicked.connect(self.accept)
        self.choose_mine_button.setEnabled(False)
        self.choose_other_button.setEnabled(False)
        self._update_resolve_enabled()

        self._populate_placeholder_rows()
        self._start_author_fetch()

    # -- rows --------------------------------------------------------------

    def _populate_placeholder_rows(self) -> None:
        """Fills File/My Username in immediately (both already known
        locally, no I/O) so the dialog isn't blank while the background
        worker fetches avatars and the other side's author per file."""
        self.table.setRowCount(len(self.conflicted_files))
        for row, file_path in enumerate(self.conflicted_files):
            self.table.setItem(row, _COL_FILE, QTableWidgetItem(file_path))
            self.table.setItem(row, _COL_MY_AVATAR, _avatar_item(None))
            self.table.setItem(row, _COL_MY_USERNAME, QTableWidgetItem(self.my_username))
            self.table.setItem(row, _COL_MY_STATUS, QTableWidgetItem())
            self.table.setItem(row, _COL_OTHER_AVATAR, _avatar_item(None))
            self.table.setItem(row, _COL_OTHER_USERNAME, QTableWidgetItem("Loading..."))
            self.table.setItem(row, _COL_OTHER_STATUS, QTableWidgetItem())

    def _start_author_fetch(self) -> None:
        self._author_worker = GitStreamWorker(lambda on_output: self._fetch_author_info())
        self._author_worker.finished_ok.connect(self._on_author_info_ready)
        self._author_worker.failed.connect(self._on_author_info_failed)
        self._author_worker.start()

    def _fetch_author_info(self) -> tuple[bytes | None, dict[str, tuple[str, bytes | None]]]:
        my_avatar = fetch_avatar_bytes(self.my_username)
        other_info: dict[str, tuple[str, bytes | None]] = {
            file_path: self._fetch_other_author(file_path) for file_path in self.conflicted_files
        }
        return my_avatar, other_info

    def _fetch_other_author(self, file_path: str) -> tuple[str, bytes | None]:
        # GitHub-API-first (path-scoped, so the top result is exactly the
        # most recent commit on the remote's default branch that touched
        # this file — i.e. MERGE_HEAD's version), local-git-fallback (same
        # approach interface/shared/commit_history.py's other callers use),
        # matching CommitLogWorker's own fallback pattern.
        entries = fetch_entries_via_github(
            self.git_service, self.repo_path, file_path, self.github_token, 1, 1, self._other_avatar_cache
        )
        if entries:
            entry = entries[0]
            return entry.author_display, entry.avatar_bytes
        commits = self.git_service.get_commit_log(self.repo_path, limit=1, ref="MERGE_HEAD", paths=[file_path])
        if commits:
            return commits[0].author, None
        return "Unknown", None

    def _on_author_info_ready(self, result: object) -> None:
        my_avatar, other_info = result
        for row, file_path in enumerate(self.conflicted_files):
            self.table.setItem(row, _COL_MY_AVATAR, _avatar_item(my_avatar))
            other_username, other_avatar = other_info.get(file_path, ("Unknown", None))
            self.table.setItem(row, _COL_OTHER_AVATAR, _avatar_item(other_avatar))
            self.table.setItem(row, _COL_OTHER_USERNAME, QTableWidgetItem(other_username))
        self.choose_mine_button.setEnabled(True)
        self.choose_other_button.setEnabled(True)

    def _on_author_info_failed(self, _message: str) -> None:
        # Best-effort display nicety — leave the "Loading..." placeholders'
        # glyph fallback in place and still let the user resolve by file
        # name alone rather than blocking conflict resolution on it.
        for row in range(self.table.rowCount()):
            self.table.setItem(row, _COL_OTHER_USERNAME, QTableWidgetItem("Unknown"))
        self.choose_mine_button.setEnabled(True)
        self.choose_other_button.setEnabled(True)

    # -- choose mine / other -------------------------------------------------

    def _apply_choice(self, keep: str) -> None:
        rows = {index.row() for index in self.table.selectionModel().selectedRows()}
        if not rows:
            return
        check_icon = self.style().standardIcon(QStyle.SP_DialogApplyButton)
        cross_icon = self.style().standardIcon(QStyle.SP_DialogCancelButton)
        for row in rows:
            file_path = self.table.item(row, _COL_FILE).text()
            self._resolutions[file_path] = keep
            mine_icon, other_icon = (check_icon, cross_icon) if keep == "ours" else (cross_icon, check_icon)
            self.table.item(row, _COL_MY_STATUS).setIcon(mine_icon)
            self.table.item(row, _COL_OTHER_STATUS).setIcon(other_icon)
        self._update_resolve_enabled()

    def _update_resolve_enabled(self) -> None:
        self.resolve_button.setEnabled(len(self._resolutions) == len(self.conflicted_files))

    def resolutions(self) -> dict[str, str]:
        return dict(self._resolutions)
