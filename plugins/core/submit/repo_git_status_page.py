from __future__ import annotations

import webbrowser
from pathlib import Path, PurePosixPath

from PySide6.QtCore import QFile, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStyle,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from plugin_api import (
    CommitFilesDialog,
    CommitHistoryEntry,
    FileChange,
    GitHubAuthError,
    GitOperationError,
    GitService,
    LocalConfigStore,
    MetadataStore,
    Project,
    Repo,
    RepoStatus,
    UkoreHubError,
    check_repo_access,
    confirm_action,
    format_commit_date,
    format_relative_time,
    open_in_file_explorer,
    show_exclusive,
    wrap_scrollable,
)
from plugins.core.submit.commit_dialog import CommitDialog
from plugins.core.submit.commit_log_worker import CommitLogWorker
from plugins.core.submit.conflict_dialog import ConflictResolutionDialog
from plugins.core.submit.git_stream_worker import GitStreamWorker
from plugins.core.submit.status_worker import RepoStatusWorker

# How long a "clean" status stays "fresh" (blue) before the freshness timer
# reverts the sidebar status dot to "loading" (no icon), pending the next
# refresh_status() call.
FRESHNESS_WINDOW_MS = 10 * 60 * 1000
# Background repoll of the commit history panel while the app just sits
# open on this tab — set_repo/refresh_status/push already trigger an
# immediate poll, this just catches teammates' pushes in between.
COMMIT_LOG_POLL_INTERVAL_MS = 30 * 60 * 1000
_STATUS_DOT_SIZE = 14
_UI_FILE = Path(__file__).resolve().parent / "submit_section.ui"

# FileChange.change_type -> what the Modified column shows.
_CHANGE_TYPE_LABELS = {
    "untracked": "Added",
    "added": "Added",
    "modified": "Modified",
    "deleted": "Removed",
    "renamed": "Renamed",
}

# Roles used to stash the real repo-relative path (and raw change_type, for
# revert's untracked/tracked split) on a Modified/Staged row's File Name
# item, so display formatting/sorting never has to be reverse-parsed.
_PATH_ROLE = Qt.UserRole + 1
_CHANGE_TYPE_ROLE = Qt.UserRole + 2


def _load_ui_form(parent: QWidget | None = None) -> QWidget:
    """Loads submit_section.ui at runtime (QUiLoader, no compile step) so a
    Designer edit to that file takes effect on the next app launch without
    rebuilding anything. Only stock Qt widget classes are used in the .ui,
    so no promoted-widget registration is needed."""
    loader = QUiLoader()
    ui_file = QFile(str(_UI_FILE))
    ui_file.open(QFile.ReadOnly)
    try:
        form = loader.load(ui_file, parent)
    finally:
        ui_file.close()
    return form


class RepoGitStatusPage(QWidget):
    sync_started = Signal()
    sync_finished = Signal()
    sync_failed = Signal(str)
    browse_file_requested = Signal(Path)

    def __init__(self, parent=None, *, store: MetadataStore, local_config_store: LocalConfigStore, git_service: GitService):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self.git_service = git_service

        self._project: Project | None = None
        self._repo: Repo | None = None
        self._workspace_root: str | None = None
        self._git_worker: GitStreamWorker | None = None
        self._status_worker: RepoStatusWorker | None = None
        self._stream_worker: GitStreamWorker | None = None
        self._stage_worker: GitStreamWorker | None = None
        self._unstage_worker: GitStreamWorker | None = None
        self._revert_worker: GitStreamWorker | None = None
        self._diagnostics_worker: GitStreamWorker | None = None
        self._commit_log_worker: CommitLogWorker | None = None
        self._commit_log_entries: list[CommitHistoryEntry] = []
        self._commit_log_avatar_cache: dict[str, bytes | None] = {}
        self._commit_files_dialog: CommitFilesDialog | None = None
        self._last_status: RepoStatus | None = None

        # Sidebar-row status indicator (SectionSpec.trailing_widget_factory —
        # see plugin.py) — a plain QLabel, no custom widget class. This page
        # owns/updates it directly via _set_status_dot_state;
        # _freshness_timer flips a "fresh" (clean, just-verified) state back
        # to "loading" once that verification is more than
        # FRESHNESS_WINDOW_MS old; every call to refresh_status() restarts
        # it. Deliberately independent of tableView_git_status's diagnostics
        # (auth/clone/up-to-date) — this only ever reflects working-tree
        # cleanliness.
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(_STATUS_DOT_SIZE, _STATUS_DOT_SIZE)
        self._freshness_timer = QTimer(self)
        self._freshness_timer.setSingleShot(True)
        self._freshness_timer.timeout.connect(lambda: self._set_status_dot_state("loading"))
        self._set_status_dot_state("loading")

        self.empty_label = QLabel("Select a repo to see this information.")

        self._ui = _load_ui_form()
        self._setup_ui_widgets()

        # Without this scroll wrapper, a window-height squeeze can shrink a
        # whole group box (border and title included) to 0 height instead of
        # just showing fewer rows — see the "Card->table rewrite" note this
        # plugin's doc keeps. Same wrap_scrollable(page content) shape as
        # project_editor/custom_paths_settings_page.py and friends.
        scroll = wrap_scrollable(self._ui)
        self.content_widget = QWidget()
        content_wrap_layout = QVBoxLayout(self.content_widget)
        content_wrap_layout.setContentsMargins(0, 0, 0, 0)
        content_wrap_layout.addWidget(scroll)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)
        self.content_widget.setVisible(False)

        self._commit_log_timer = QTimer(self)
        self._commit_log_timer.setInterval(COMMIT_LOG_POLL_INTERVAL_MS)
        self._commit_log_timer.timeout.connect(self._poll_commit_log)
        self._commit_log_timer.start()

    # -- .ui wiring -----------------------------------------------------

    def _setup_ui_widgets(self) -> None:
        find = self._ui.findChild
        self.sync_button: QPushButton = find(QPushButton, "pushButton_sync")
        self.refresh_button: QPushButton = find(QPushButton, "pushButton_refresh_status")
        self.plain_text_git_log: QPlainTextEdit = find(QPlainTextEdit, "plainTextEdit_git_log")
        self.plain_text_git_log.setMaximumBlockCount(5000)

        self.table_git_status: QTableView = find(QTableView, "tableView_git_status")
        self.table_modified: QTableView = find(QTableView, "tableView_modified")
        self.table_staged: QTableView = find(QTableView, "tableView_staged")
        self.table_commit_history: QTableView = find(QTableView, "tableView_commit_history")

        self.revert_button: QPushButton = find(QPushButton, "pushButton_revert")
        self.stage_button: QPushButton = find(QPushButton, "pushButton_stage")
        self.unstage_button: QPushButton = find(QPushButton, "pushButton_unstage")
        self.submit_all_staged_button: QPushButton = find(QPushButton, "pushButton_submit_all_staged")
        self.local_dir_button: QPushButton = find(QPushButton, "pushButton_local_dir")
        self.repo_website_button: QPushButton = find(QPushButton, "pushButton_repo_website")

        self.modified_model = QStandardItemModel(0, 3, self)
        self.modified_model.setHorizontalHeaderLabels(["File Name", "File Path", "Modified"])
        self.table_modified.setModel(self.modified_model)

        self.staged_model = QStandardItemModel(0, 3, self)
        self.staged_model.setHorizontalHeaderLabels(["File Name", "File Path", "Modified"])
        self.table_staged.setModel(self.staged_model)

        for table in (self.table_modified, self.table_staged):
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setSelectionMode(QAbstractItemView.ExtendedSelection)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.verticalHeader().setVisible(False)
            table.setContextMenuPolicy(Qt.CustomContextMenu)
            table.customContextMenuRequested.connect(lambda pos, t=table: self._show_inspect_menu(t, pos))
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.git_status_model = QStandardItemModel(0, 3, self)
        self.git_status_model.setHorizontalHeaderLabels(["Name", "Detail", "Status"])
        self.table_git_status.setModel(self.git_status_model)
        self.table_git_status.setSelectionMode(QAbstractItemView.NoSelection)
        self.table_git_status.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_git_status.verticalHeader().setVisible(False)
        status_header = self.table_git_status.horizontalHeader()
        status_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        status_header.setSectionResizeMode(1, QHeaderView.Stretch)
        status_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.commit_log_model = QStandardItemModel(0, 5, self)
        self.commit_log_model.setHorizontalHeaderLabels(["", "Author", "Message", "Time Ago", "Date"])
        self.table_commit_history.setModel(self.commit_log_model)
        self.table_commit_history.setSelectionMode(QAbstractItemView.NoSelection)
        self.table_commit_history.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_commit_history.verticalHeader().setVisible(False)
        self.table_commit_history.setIconSize(QSize(20, 20))
        history_header = self.table_commit_history.horizontalHeader()
        history_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        history_header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_commit_history.doubleClicked.connect(self._on_commit_row_double_clicked)

        self.sync_button.clicked.connect(self.start_sync)
        self.refresh_button.clicked.connect(self.refresh_status)
        self.stage_button.clicked.connect(self._on_stage_clicked)
        self.revert_button.clicked.connect(self._on_revert_clicked)
        self.unstage_button.clicked.connect(self._on_unstage_clicked)
        self.submit_all_staged_button.clicked.connect(self._on_submit_all_staged_clicked)
        self.local_dir_button.clicked.connect(self._on_local_dir_clicked)
        self.repo_website_button.clicked.connect(self._on_repo_website_clicked)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        self._workspace_root = workspace_root
        if repo is None:
            self._freshness_timer.stop()
            self._set_status_dot_state("loading")
            show_exclusive(self.empty_label, self.content_widget)
            return
        show_exclusive(self.content_widget, self.empty_label)
        self.refresh_status()

    def sync_active_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        """Optional MainWindow generic-startup protocol — see
        interface/main_window.py's _start_auto_sync, which calls this on
        whichever registered page(s) implement it (today: just this one)."""
        self.set_repo(project, repo, workspace_root)
        self.start_sync()

    def _dest_path(self) -> Path:
        return Path(self._workspace_root) / self._repo.local_path

    def _append_log(self, text: str) -> None:
        self.plain_text_git_log.appendPlainText(text)
        scrollbar = self.plain_text_git_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _set_status_dot_state(self, state: str) -> None:
        if state == "loading":
            self.status_dot.setVisible(False)
            return
        standard_icon = QStyle.SP_MessageBoxWarning if state == "dirty" else QStyle.SP_DialogApplyButton
        icon = self.style().standardIcon(standard_icon)
        self.status_dot.setPixmap(icon.pixmap(_STATUS_DOT_SIZE, _STATUS_DOT_SIZE))
        self.status_dot.setToolTip("Uncommitted changes" if state == "dirty" else "Up to date")
        self.status_dot.setVisible(True)

    # -- status (Modified / Staged tables + diagnostics) -----------------

    def refresh_status(self) -> None:
        if self._repo is None or self._workspace_root is None:
            return
        # Every refresh (Sync, Refresh Status, repo switch/auto-sync — the
        # only triggers this dot reacts to) starts out "loading" until the
        # new check reports back, so the dot never shows a stale/wrong-repo
        # color while a fresh one is in flight.
        self._freshness_timer.stop()
        self._set_status_dot_state("loading")
        dest_path = self._dest_path()
        if not (dest_path / ".git").exists():
            self.modified_model.removeRows(0, self.modified_model.rowCount())
            self.staged_model.removeRows(0, self.staged_model.rowCount())
            return
        self._poll_commit_log()
        self._run_diagnostics()
        if self._status_worker is not None and self._status_worker.isRunning():
            # A previous refresh is still in flight (e.g. rapid clicks on
            # Refresh Status/tab switches) — don't orphan it mid-run, which
            # crashes the app when its QThread object gets garbage collected
            # while still alive. Just let the in-flight one finish.
            return
        self._status_worker = RepoStatusWorker(self.git_service, dest_path)
        self._status_worker.status_ready.connect(self._on_status_ready)
        self._status_worker.failed.connect(self._on_status_failed)
        self._status_worker.start()

    def _on_status_ready(self, status: RepoStatus) -> None:
        self._last_status = status
        self._populate_file_table(self.modified_model, status.unstaged_changes)
        self._populate_file_table(self.staged_model, status.staged_changes)
        if status.is_clean:
            self._set_status_dot_state("fresh")
            self._freshness_timer.start(FRESHNESS_WINDOW_MS)
        else:
            self._set_status_dot_state("dirty")

    def _on_status_failed(self, message: str) -> None:
        self._append_log(f"--- Failed to read status: {message} ---")

    def _populate_file_table(self, model: QStandardItemModel, changes: list[FileChange]) -> None:
        model.removeRows(0, model.rowCount())
        for change in sorted(changes, key=lambda c: c.path):
            pure_path = PurePosixPath(change.path)
            name_item = QStandardItem(pure_path.name)
            name_item.setData(change.path, _PATH_ROLE)
            name_item.setData(change.change_type, _CHANGE_TYPE_ROLE)
            parent = str(pure_path.parent)
            path_item = QStandardItem("" if parent == "." else parent)
            type_item = QStandardItem(_CHANGE_TYPE_LABELS.get(change.change_type, change.change_type.title()))
            model.appendRow([name_item, path_item, type_item])

    def _selected_rows_data(self, table: QTableView, model: QStandardItemModel) -> list[tuple[str, str]]:
        rows = {index.row() for index in table.selectionModel().selectedRows()}
        return [
            (model.item(row, 0).data(_PATH_ROLE), model.item(row, 0).data(_CHANGE_TYPE_ROLE)) for row in sorted(rows)
        ]

    def _show_inspect_menu(self, table: QTableView, pos) -> None:
        index = table.indexAt(pos)
        if not index.isValid() or self._repo is None:
            return
        path = table.model().item(index.row(), 0).data(_PATH_ROLE)
        menu = QMenu(self)
        inspect_action = menu.addAction("Inspect in Explorer")
        action = menu.exec(table.viewport().mapToGlobal(pos))
        if action == inspect_action:
            self.browse_file_requested.emit(self._dest_path() / path)

    # -- diagnostics table (Token & Auth / Clone / Up-to-date) ------------

    def _run_diagnostics(self) -> None:
        if self._repo is None:
            return
        if self._diagnostics_worker is not None and self._diagnostics_worker.isRunning():
            # Same "don't orphan an in-flight worker" guard every other
            # worker on this page uses.
            return
        repo = self._repo
        dest_path = self._dest_path()
        git_service = self.git_service

        def action(_on_output):
            results: list[tuple[str, str, bool]] = []

            token = git_service.get_github_token()
            owner_repo = git_service.parse_github_owner_repo(repo.git_url)
            if token is None:
                results.append(("Token & Auth", "No GitHub token found — please log in.", False))
            elif owner_repo is not None:
                try:
                    has_access = check_repo_access(owner_repo[0], owner_repo[1], token)
                    detail = (
                        "Authenticated, repo access confirmed."
                        if has_access
                        else f"No access to {owner_repo[0]}/{owner_repo[1]}."
                    )
                    results.append(("Token & Auth", detail, has_access))
                except GitHubAuthError as exc:
                    results.append(("Token & Auth", str(exc), False))
            else:
                results.append(("Token & Auth", "Token present (non-GitHub remote, access not checked).", True))

            is_cloned = git_service.is_cloned(dest_path)
            results.append(
                ("Clone", "Repo cloned and .git present." if is_cloned else "Repo not cloned locally.", is_cloned)
            )

            if is_cloned:
                try:
                    git_service.fetch(dest_path)
                except GitOperationError:
                    pass  # offline/auth hiccup — fall back to whatever's already local
                ahead_behind = git_service.get_ahead_behind(dest_path)
                if ahead_behind is None:
                    results.append(("Up-to-date", "No upstream branch configured.", False))
                else:
                    ahead, behind = ahead_behind
                    if behind > 0:
                        results.append(("Up-to-date", f"{behind} commit(s) behind origin — sync to update.", False))
                    else:
                        detail = (
                            "Up to date."
                            if ahead == 0
                            else f"Up to date locally, {ahead} commit(s) ahead (not yet pushed)."
                        )
                        results.append(("Up-to-date", detail, True))
            else:
                results.append(("Up-to-date", "Not cloned yet.", False))

            return results

        self._diagnostics_worker = GitStreamWorker(action)
        self._diagnostics_worker.finished_ok.connect(self._on_diagnostics_ready)
        self._diagnostics_worker.failed.connect(
            lambda message: self._append_log(f"--- Diagnostics check failed: {message} ---")
        )
        self._diagnostics_worker.start()

    def _on_diagnostics_ready(self, results: list[tuple[str, str, bool]]) -> None:
        self.git_status_model.removeRows(0, self.git_status_model.rowCount())
        for name, detail, ok in results:
            name_item = QStandardItem(name)
            detail_item = QStandardItem(detail)
            status_item = QStandardItem()
            standard_icon = QStyle.SP_DialogApplyButton if ok else QStyle.SP_MessageBoxWarning
            status_item.setIcon(self.style().standardIcon(standard_icon))
            self.git_status_model.appendRow([name_item, detail_item, status_item])

    # -- commit history panel ------------------------------------------------

    def _poll_commit_log(self) -> None:
        if self._repo is None or self._workspace_root is None:
            return
        if self._commit_log_worker is not None and self._commit_log_worker.isRunning():
            # A previous poll is still in flight — don't orphan it mid-run
            # (same guard every other worker on this page uses); the next
            # trigger (timer/refresh/push) will pick up whatever changed.
            return
        dest_path = self._dest_path()
        if not self.git_service.is_cloned(dest_path):
            return
        self._commit_log_worker = CommitLogWorker(
            self.git_service, dest_path, self.git_service.get_github_token(), avatar_cache=self._commit_log_avatar_cache
        )
        self._commit_log_worker.entries_ready.connect(self._on_commit_log_ready)
        self._commit_log_worker.start()

    def _on_commit_log_ready(self, entries: list[CommitHistoryEntry]) -> None:
        self._commit_log_entries = entries
        self.commit_log_model.removeRows(0, self.commit_log_model.rowCount())
        for entry in entries:
            avatar_item = QStandardItem()
            if entry.avatar_bytes:
                pixmap = QPixmap()
                pixmap.loadFromData(entry.avatar_bytes)
                avatar_item.setIcon(QIcon(pixmap))
            else:
                # No avatar (local-git fallback, or the download failed) —
                # same generic person glyph the previous CommitCard-based
                # panel fell back to.
                avatar_item.setText("\U0001F464")
                avatar_item.setTextAlignment(Qt.AlignCenter)
            self.commit_log_model.appendRow(
                [
                    avatar_item,
                    QStandardItem(entry.author_display),
                    QStandardItem(entry.message),
                    QStandardItem(format_relative_time(entry.date)),
                    QStandardItem(format_commit_date(entry.date)),
                ]
            )

    def _on_commit_row_double_clicked(self, index) -> None:
        row = index.row()
        if not (0 <= row < len(self._commit_log_entries)):
            return
        # Non-modal, fresh dialog per double-click — replaces the previous
        # one (if a row was already open) rather than stacking windows.
        if self._commit_files_dialog is not None:
            self._commit_files_dialog.close()
        self._commit_files_dialog = CommitFilesDialog(
            self,
            git_service=self.git_service,
            repo_path=self._dest_path(),
            entry=self._commit_log_entries[row],
            on_browse_file=self.browse_file_requested.emit,
        )
        # WA_DeleteOnClose destroys the underlying C++ object as soon as the
        # dialog is closed (including via the window's own X button), but
        # this Python attribute would otherwise keep pointing at it — the
        # next double-click's .close() call above would then raise on the
        # already-deleted object and never reach dialog creation.
        self._commit_files_dialog.finished.connect(self._on_commit_files_dialog_finished)
        self._commit_files_dialog.show()

    def _on_commit_files_dialog_finished(self) -> None:
        self._commit_files_dialog = None

    def _on_repo_website_clicked(self) -> None:
        if self._repo is None:
            return
        owner_repo = self.git_service.parse_github_owner_repo(self._repo.git_url)
        if owner_repo is None:
            QMessageBox.warning(self, "Repo Site", "This repo's remote isn't a github.com URL.")
            return
        owner, name = owner_repo
        webbrowser.open(f"https://github.com/{owner}/{name}")

    def _on_local_dir_clicked(self) -> None:
        if self._repo is None:
            return
        open_in_file_explorer(self._dest_path())

    # -- stage / unstage / revert (multi-selection) --------------------------

    def _on_stage_clicked(self) -> None:
        if self._repo is None:
            return
        paths = [path for path, _ in self._selected_rows_data(self.table_modified, self.modified_model)]
        if not paths:
            return
        if self._stage_worker is not None and self._stage_worker.isRunning():
            # Same "don't orphan an in-flight worker" guard as start_sync /
            # refresh_status — a rapid second click would otherwise crash the
            # app when this QThread object gets garbage collected mid-run.
            return
        dest_path = self._dest_path()
        self.stage_button.setEnabled(False)
        self._stage_worker = GitStreamWorker(lambda on_output: self.git_service.stage_paths(dest_path, paths))
        self._stage_worker.finished_ok.connect(self._on_stage_finished)
        self._stage_worker.failed.connect(self._on_stage_failed)
        self._stage_worker.start()

    def _on_stage_finished(self, _result: object) -> None:
        self.stage_button.setEnabled(True)
        self.refresh_status()

    def _on_stage_failed(self, message: str) -> None:
        self.stage_button.setEnabled(True)
        QMessageBox.warning(self, "Stage Failed", message)

    def _on_unstage_clicked(self) -> None:
        if self._repo is None:
            return
        paths = [path for path, _ in self._selected_rows_data(self.table_staged, self.staged_model)]
        if not paths:
            return
        if self._unstage_worker is not None and self._unstage_worker.isRunning():
            return
        dest_path = self._dest_path()
        self.unstage_button.setEnabled(False)
        self._unstage_worker = GitStreamWorker(lambda on_output: self.git_service.unstage_paths(dest_path, paths))
        self._unstage_worker.finished_ok.connect(self._on_unstage_finished)
        self._unstage_worker.failed.connect(self._on_unstage_failed)
        self._unstage_worker.start()

    def _on_unstage_finished(self, _result: object) -> None:
        self.unstage_button.setEnabled(True)
        self.refresh_status()

    def _on_unstage_failed(self, message: str) -> None:
        self.unstage_button.setEnabled(True)
        QMessageBox.warning(self, "Restore Failed", message)

    def _on_revert_clicked(self) -> None:
        if self._repo is None:
            return
        selected = self._selected_rows_data(self.table_modified, self.modified_model)
        if not selected:
            return
        confirmed = confirm_action(
            self,
            "Revert",
            f"Revert {len(selected)} selected file(s)? This discards their changes and cannot be undone.",
        )
        if not confirmed:
            return
        if self._revert_worker is not None and self._revert_worker.isRunning():
            return
        untracked_paths = [path for path, change_type in selected if change_type == "untracked"]
        modified_paths = [path for path, change_type in selected if change_type != "untracked"]
        dest_path = self._dest_path()
        self.revert_button.setEnabled(False)
        self._revert_worker = GitStreamWorker(
            lambda on_output: self.git_service.revert_paths(
                dest_path, modified_paths=modified_paths, untracked_paths=untracked_paths
            )
        )
        self._revert_worker.finished_ok.connect(self._on_revert_finished)
        self._revert_worker.failed.connect(self._on_revert_failed)
        self._revert_worker.start()

    def _on_revert_finished(self, _result: object) -> None:
        self.revert_button.setEnabled(True)
        self.refresh_status()

    def _on_revert_failed(self, message: str) -> None:
        self.revert_button.setEnabled(True)
        QMessageBox.warning(self, "Revert Failed", message)

    # -- sync (clone/pull, unchanged) ----------------------------------------

    def start_sync(self) -> None:
        if self._repo is None or self._workspace_root is None:
            return
        if self._git_worker is not None and self._git_worker.isRunning():
            # A previous sync is still in flight (e.g. rapid repo switches
            # via Project Editor's node double-click, each of which calls
            # sync_active_repo -> start_sync again) — don't orphan it
            # mid-run, which crashes the app when its QThread object gets
            # garbage collected while still alive. Just let the in-flight
            # one finish (same guard refresh_status() already has for
            # _status_worker, below).
            return
        dest_path = self._dest_path()
        self.sync_button.setEnabled(False)
        self.sync_started.emit()

        if not self.git_service.is_cloned(dest_path):
            # Only relevant before the very first clone — once a repo is
            # cloned, ordinary pull/push failures already surface through
            # _on_sync_failed. Checking here means a private repo the
            # current GitHub account can't see gets a clear "contact your
            # admin" dialog up front instead of git's own opaque clone
            # error after it's already tried and failed.
            owner_repo = self.git_service.parse_github_owner_repo(self._repo.git_url)
            if owner_repo is not None:
                self._append_log(f"--- Checking access to '{self._repo.name}' ---")
                self._begin_access_check(owner_repo, dest_path)
                return
        self._begin_sync_worker(dest_path)

    def _begin_access_check(self, owner_repo: tuple[str, str], dest_path: Path) -> None:
        owner, name = owner_repo
        token = self.git_service.get_github_token()

        def action(_on_output):
            try:
                return check_repo_access(owner, name, token)
            except GitHubAuthError:
                # Can't verify (network hiccup, rate limit, ...) — don't
                # block the sync on an unrelated failure, just fall through
                # to the real clone attempt as before this check existed.
                return True

        self._git_worker = GitStreamWorker(action)
        self._git_worker.finished_ok.connect(
            lambda has_access: self._on_access_checked(has_access, owner, name, dest_path)
        )
        self._git_worker.failed.connect(self._on_sync_failed)
        self._git_worker.start()

    def _on_access_checked(self, has_access: bool, owner: str, name: str, dest_path: Path) -> None:
        if not has_access:
            self.sync_button.setEnabled(True)
            self._append_log(f"--- Access denied to '{owner}/{name}' ---")
            QMessageBox.warning(
                self,
                "Access Denied",
                f"Your GitHub account doesn't have access to '{owner}/{name}'.\n\n"
                "Please contact your admin to request access to this repository.",
            )
            self.sync_failed.emit(f"No access to {owner}/{name}")
            return
        self._begin_sync_worker(dest_path)

    def _begin_sync_worker(self, dest_path: Path) -> None:
        self._append_log(f"--- Syncing '{self._repo.name}' ---")
        self._git_worker = GitStreamWorker(
            lambda on_output: self.git_service.open_or_sync(self._repo.git_url, dest_path, on_output=on_output)
        )
        self._git_worker.output.connect(self._append_log)
        self._git_worker.finished_ok.connect(self._on_sync_finished)
        self._git_worker.failed.connect(self._on_sync_failed)
        self._git_worker.start()

    def _on_sync_finished(self, status: str) -> None:
        self.sync_button.setEnabled(True)
        try:
            self.store.mark_synced(self._project.id, self._repo.id, "cloned")
        except UkoreHubError:
            pass
        self._append_log(f"--- Done ({status}) ---")
        self.refresh_status()
        self.sync_finished.emit()

    def _on_sync_failed(self, message: str) -> None:
        self.sync_button.setEnabled(True)
        try:
            self.store.mark_status(self._project.id, self._repo.id, "error")
        except UkoreHubError:
            pass
        self._append_log(f"--- Failed: {message} ---")
        QMessageBox.warning(self, "Sync Failed", message)
        self.sync_failed.emit(message)

    # -- commit -> pull -> (resolve conflicts) -> push -----------------------

    def _on_submit_all_staged_clicked(self) -> None:
        if self._repo is None:
            return
        dialog = CommitDialog(self)
        if not dialog.exec():
            return
        message = dialog.message()
        amend = dialog.amend()

        dest_path = self._dest_path()
        try:
            self.git_service.commit(dest_path, message, amend=amend)
        except GitOperationError as exc:
            QMessageBox.warning(self, "Commit Failed", str(exc))
            return
        self._append_log("--- Committed ---")
        self._start_pull_step()

    def _set_workflow_running(self, running: bool) -> None:
        self.submit_all_staged_button.setEnabled(not running)
        self.stage_button.setEnabled(not running)
        self.unstage_button.setEnabled(not running)

    def _start_pull_step(self) -> None:
        dest_path = self._dest_path()
        self._append_log("--- Pulling ---")
        self._set_workflow_running(True)
        self._stream_worker = GitStreamWorker(
            lambda on_output: self.git_service.pull(dest_path, on_output=on_output)
        )
        self._stream_worker.output.connect(self._append_log)
        self._stream_worker.finished_ok.connect(self._on_pull_step_finished)
        self._stream_worker.failed.connect(self._on_pull_step_failed)
        self._stream_worker.start()

    def _on_pull_step_finished(self) -> None:
        self._append_log("--- Pull done ---")
        self._start_push_step()

    def _on_pull_step_failed(self, message: str) -> None:
        dest_path = self._dest_path()
        if not self.git_service.has_unresolved_merge(dest_path):
            self._set_workflow_running(False)
            self._append_log(f"--- Pull failed: {message} ---")
            QMessageBox.warning(self, "Pull Failed", message)
            return
        self._append_log("--- Merge conflict detected ---")
        conflicted = self.git_service.get_conflicted_files(dest_path)
        dialog = ConflictResolutionDialog(self, conflicted_files=conflicted)
        if not dialog.exec():
            self._set_workflow_running(False)
            self._append_log("--- Conflicts left unresolved — resolve and try again ---")
            return
        resolutions = dialog.resolutions()
        try:
            for file_path, keep in resolutions.items():
                self.git_service.resolve_conflict_file(dest_path, file_path, keep)
            self.git_service.complete_merge(dest_path)
        except GitOperationError as exc:
            self._set_workflow_running(False)
            QMessageBox.warning(self, "Conflict Resolution Failed", str(exc))
            return
        self._append_log("--- Conflicts resolved, merge completed ---")
        self._start_push_step()

    def _start_push_step(self) -> None:
        dest_path = self._dest_path()
        self._append_log("--- Pushing ---")
        self._stream_worker = GitStreamWorker(
            lambda on_output: self.git_service.push(dest_path, on_output=on_output)
        )
        self._stream_worker.output.connect(self._append_log)
        self._stream_worker.finished_ok.connect(self._on_push_finished)
        self._stream_worker.failed.connect(self._on_push_failed)
        self._stream_worker.start()

    def _on_push_finished(self) -> None:
        self._set_workflow_running(False)
        self._append_log("--- Push done ---")
        self.refresh_status()

    def _on_push_failed(self, message: str) -> None:
        self._set_workflow_running(False)
        self._append_log(f"--- Push failed: {message} ---")
        QMessageBox.warning(self, "Push Failed", message)
