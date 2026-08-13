from __future__ import annotations

import webbrowser
from pathlib import Path

from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plugin_api import (
    CommitFilesDialog,
    CommitHistoryEntry,
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
    show_exclusive,
    wrap_scrollable,
)
from plugins.core.submit.commit_dialog import CommitDialog
from plugins.core.submit.commit_log_worker import CommitLogWorker
from plugins.core.submit.conflict_dialog import ConflictResolutionDialog
from plugins.core.submit.git_stream_worker import GitStreamWorker
from plugins.core.submit.log_panel import LogPanel
from plugins.core.submit.status_dot import RepoStatusDot
from plugins.core.submit.status_worker import RepoStatusWorker

# How long a "clean" status stays "fresh" (blue) before _freshness_timer
# reverts RepoStatusDot to "loading" (no icon), pending the next
# refresh_status() call.
FRESHNESS_WINDOW_MS = 10 * 60 * 1000
# Background repoll of the commit history panel while the app just sits
# open on this tab — set_repo/refresh_status/push already trigger an
# immediate poll, this just catches teammates' pushes in between.
COMMIT_LOG_POLL_INTERVAL_MS = 30 * 60 * 1000


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
        self._commit_log_worker: CommitLogWorker | None = None
        self._commit_log_entries: list[CommitHistoryEntry] = []
        self._commit_log_avatar_cache: dict[str, bytes | None] = {}
        self._commit_files_dialog: CommitFilesDialog | None = None
        self._pending_commit_message = ""
        self._pending_amend = False
        self._last_status: RepoStatus | None = None

        # Sidebar-row status indicator (SectionSpec.trailing_widget_factory —
        # see plugin.py) — this page owns/updates it directly.
        # _freshness_timer flips a
        # "fresh" (clean, just-verified) dot back to "loading" once that
        # verification is more than FRESHNESS_WINDOW_MS old; every call to
        # refresh_status() restarts it.
        self.status_dot = RepoStatusDot()
        self._freshness_timer = QTimer(self)
        self._freshness_timer.setSingleShot(True)
        self._freshness_timer.timeout.connect(lambda: self.status_dot.set_state("loading"))

        self.empty_label = QLabel("Select a repo to see this information.")

        lists_row = QHBoxLayout()

        # Checkable items instead of row selection — lets the user tick
        # several files without holding Ctrl/Shift, then Stage/Revert acts
        # on whatever's checked (see _checked_modified_paths).
        self.modified_list = QListWidget()
        self.modified_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.modified_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.modified_list.customContextMenuRequested.connect(
            lambda pos: self._show_inspect_menu(self.modified_list, pos)
        )
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(
            lambda: self._on_select_all_clicked(self.modified_list)
        )
        self.stage_button = QPushButton("Stage")
        self.stage_button.clicked.connect(self._on_stage_clicked)
        self.revert_button = QPushButton("Revert")
        self.revert_button.clicked.connect(self._on_revert_clicked)
        modified_button_row = QHBoxLayout()
        modified_button_row.addWidget(self.select_all_button)
        modified_button_row.addWidget(self.stage_button)
        modified_button_row.addWidget(self.revert_button)
        modified_group = QGroupBox("Modified")
        modified_layout = QVBoxLayout(modified_group)
        modified_layout.addWidget(self.modified_list)
        modified_layout.addLayout(modified_button_row)
        lists_row.addWidget(modified_group)

        self.staged_list = QListWidget()
        self.staged_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.staged_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.staged_list.customContextMenuRequested.connect(
            lambda pos: self._show_inspect_menu(self.staged_list, pos)
        )
        self.staged_select_all_button = QPushButton("Select All")
        self.staged_select_all_button.clicked.connect(
            lambda: self._on_select_all_clicked(self.staged_list)
        )
        self.restore_button = QPushButton("Restore")
        self.restore_button.clicked.connect(self._on_restore_clicked)
        self.pull_push_button = QPushButton("Pull and Push")
        self.pull_push_button.clicked.connect(self._on_pull_and_push_clicked)
        staged_button_row = QHBoxLayout()
        staged_button_row.addWidget(self.staged_select_all_button)
        staged_button_row.addWidget(self.restore_button)
        staged_button_row.addWidget(self.pull_push_button)
        # Indeterminate busy bar shown while a stage runs on _stage_worker
        # (off the UI thread — a large "Select All" batch can take a while
        # with core.git_service's chunked git-add calls) — same widget/idiom
        # as self.progress_bar below for Sync, just scoped to this group.
        self.staged_progress_bar = QProgressBar()
        self.staged_progress_bar.setRange(0, 0)
        self.staged_progress_bar.setFixedHeight(4)
        self.staged_progress_bar.setTextVisible(False)
        self.staged_progress_bar.setVisible(False)

        staged_group = QGroupBox("Staged")
        staged_layout = QVBoxLayout(staged_group)
        staged_layout.addWidget(self.staged_progress_bar)
        staged_layout.addWidget(self.staged_list)
        staged_layout.addLayout(staged_button_row)
        lists_row.addWidget(staged_group)

        self.sync_button = QPushButton("Sync")
        self.sync_button.clicked.connect(self.start_sync)
        self.refresh_button = QPushButton("Refresh Status")
        self.refresh_button.clicked.connect(self.refresh_status)
        self.gitweb_button = QPushButton("GitWeb")
        self.gitweb_button.clicked.connect(self._on_gitweb_clicked)

        button_row = QHBoxLayout()
        button_row.addWidget(self.sync_button)
        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.gitweb_button)
        button_row.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)

        self.log_panel = LogPanel()

        git_log_group = QGroupBox("Git Log")
        git_log_layout = QVBoxLayout(git_log_group)
        git_log_layout.addWidget(self.progress_bar)
        git_log_layout.addWidget(self.log_panel)
        git_log_layout.addLayout(button_row)

        # Whole-repo commit history — every teammate's pushes, not just this
        # machine's own. Polled on repo switch, Refresh Status, and after a
        # push (all funneled through refresh_status()/_poll_commit_log), plus
        # a background QTimer so it stays current while the tab just sits
        # open. Plain table, not CommitCard (interface/shared/commit_history.py)
        # — double-clicking a row opens the same CommitFilesDialog CommitCard's
        # "Files" button does.
        self.commit_log_status_label = QLabel("")
        self.commit_log_status_label.setWordWrap(True)
        # Columns: avatar icon, author, message, relative time ("3 hours
        # ago"), absolute date — date last since the relative column is the
        # one worth reading at a glance, absolute is just backup detail.
        self.commit_log_table = QTableWidget(0, 5)
        self.commit_log_table.setHorizontalHeaderLabels(["", "Author", "Message", "Time Ago", "Date"])
        self.commit_log_table.verticalHeader().setVisible(False)
        self.commit_log_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.commit_log_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.commit_log_table.setIconSize(QSize(20, 20))
        self.commit_log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.commit_log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.commit_log_table.doubleClicked.connect(self._on_commit_row_double_clicked)
        commit_log_group = QGroupBox("Commit History")
        commit_log_layout = QVBoxLayout(commit_log_group)
        commit_log_layout.addWidget(self.commit_log_status_label)
        commit_log_layout.addWidget(self.commit_log_table)

        self._commit_log_timer = QTimer(self)
        self._commit_log_timer.setInterval(COMMIT_LOG_POLL_INTERVAL_MS)
        self._commit_log_timer.timeout.connect(self._poll_commit_log)
        self._commit_log_timer.start()

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addLayout(lists_row)
        content_layout.addWidget(git_log_group)
        content_layout.addWidget(commit_log_group, 1)

        # Without this outer scroll wrapper, content_layout has no room to
        # spare on a typical window height: Modified/Staged/Git Log all get
        # the default stretch (0, "keep my sizeHint"), so Qt satisfies them
        # first and squeezes the one item stretch=1 was meant to *grow*
        # (commit_log_group) all the way down to 0 height under space
        # pressure instead — the whole "Commit History" box disappears
        # rather than just showing fewer cards. Same wrap_scrollable(page
        # content) shape as custom_paths_settings_page.py and friends.
        scroll = wrap_scrollable(content)

        self.content_widget = QWidget()
        content_wrap_layout = QVBoxLayout(self.content_widget)
        content_wrap_layout.setContentsMargins(0, 0, 0, 0)
        content_wrap_layout.addWidget(scroll)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)
        self.content_widget.setVisible(False)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        self._workspace_root = workspace_root
        if repo is None:
            self._freshness_timer.stop()
            self.status_dot.set_state("loading")
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

    def _dest_path(self):
        return Path(self._workspace_root) / self._repo.local_path

    def refresh_status(self) -> None:
        if self._repo is None or self._workspace_root is None:
            return
        # Every refresh (Sync, Refresh Status, repo switch/auto-sync — the
        # only triggers this dot reacts to) starts out "loading" until the
        # new check reports back, so the dot never shows a stale/wrong-repo
        # color while a fresh one is in flight.
        self._freshness_timer.stop()
        self.status_dot.set_state("loading")
        dest_path = self._dest_path()
        if not (dest_path / ".git").exists():
            self.modified_list.clear()
            self.staged_list.clear()
            return
        self._poll_commit_log()
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
        self.modified_list.clear()
        for path in sorted(status.untracked + status.modified):
            item = QListWidgetItem(path)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.modified_list.addItem(item)
        self.staged_list.clear()
        for path in sorted(status.staged):
            item = QListWidgetItem(path)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.staged_list.addItem(item)
        if status.is_clean:
            self.status_dot.set_state("fresh")
            self._freshness_timer.start(FRESHNESS_WINDOW_MS)
        else:
            self.status_dot.set_state("dirty")

    def _on_status_failed(self, message: str) -> None:
        self.log_panel.append_line(f"--- Failed to read status: {message} ---")

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
        self.commit_log_status_label.setText("Loading...")
        self._commit_log_worker = CommitLogWorker(
            self.git_service, dest_path, self.git_service.get_github_token(), avatar_cache=self._commit_log_avatar_cache
        )
        self._commit_log_worker.entries_ready.connect(self._on_commit_log_ready)
        self._commit_log_worker.start()

    def _on_commit_log_ready(self, entries: list[CommitHistoryEntry]) -> None:
        self._commit_log_entries = entries
        self.commit_log_status_label.setText("No commit history found." if not entries else "")
        self.commit_log_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            avatar_item = QTableWidgetItem()
            if entry.avatar_bytes:
                pixmap = QPixmap()
                pixmap.loadFromData(entry.avatar_bytes)
                avatar_item.setIcon(QIcon(pixmap))
            else:
                # No avatar (local-git fallback, or the download failed) —
                # same generic person glyph CommitCard falls back to.
                avatar_item.setText("\U0001F464")
                avatar_item.setTextAlignment(Qt.AlignCenter)
            self.commit_log_table.setItem(row, 0, avatar_item)
            self.commit_log_table.setItem(row, 1, QTableWidgetItem(entry.author_display))
            self.commit_log_table.setItem(row, 2, QTableWidgetItem(entry.message))
            self.commit_log_table.setItem(row, 3, QTableWidgetItem(format_relative_time(entry.date)))
            self.commit_log_table.setItem(row, 4, QTableWidgetItem(format_commit_date(entry.date)))

    def _on_commit_row_double_clicked(self, index) -> None:
        row = index.row()
        if not (0 <= row < len(self._commit_log_entries)):
            return
        # Non-modal, fresh dialog per double-click — replaces the previous
        # one (if a row was already open) rather than stacking windows, same
        # idiom CommitCard's own "Files" button uses.
        if self._commit_files_dialog is not None:
            self._commit_files_dialog.close()
        self._commit_files_dialog = CommitFilesDialog(
            self,
            git_service=self.git_service,
            repo_path=self._dest_path(),
            entry=self._commit_log_entries[row],
            on_browse_file=self.browse_file_requested.emit,
        )
        self._commit_files_dialog.show()

    def _on_gitweb_clicked(self) -> None:
        if self._repo is None:
            return
        owner_repo = self.git_service.parse_github_owner_repo(self._repo.git_url)
        if owner_repo is None:
            QMessageBox.warning(self, "GitWeb", "This repo's remote isn't a github.com URL.")
            return
        owner, name = owner_repo
        webbrowser.open(f"https://github.com/{owner}/{name}")

    # -- stage / unstage / revert --------------------------------------------

    def _checked_paths(self, list_widget: QListWidget) -> list[str]:
        return [
            list_widget.item(i).text()
            for i in range(list_widget.count())
            if list_widget.item(i).checkState() == Qt.Checked
        ]

    def _checked_modified_paths(self) -> list[str]:
        return self._checked_paths(self.modified_list)

    def _on_select_all_clicked(self, list_widget: QListWidget) -> None:
        # Toggle: if everything's already checked, the button clears
        # instead — one button covers both directions rather than needing
        # a separate "Deselect All". Shared by both the Modified and Staged
        # panels' Select All buttons.
        count = list_widget.count()
        all_checked = count > 0 and len(self._checked_paths(list_widget)) == count
        new_state = Qt.Unchecked if all_checked else Qt.Checked
        for i in range(count):
            list_widget.item(i).setCheckState(new_state)

    def _on_stage_clicked(self) -> None:
        selected = self._checked_modified_paths()
        if not selected or self._repo is None:
            return
        if self._stage_worker is not None and self._stage_worker.isRunning():
            # Same "don't orphan an in-flight worker" guard as start_sync /
            # refresh_status — a rapid second click would otherwise crash the
            # app when this QThread object gets garbage collected mid-run.
            return
        dest_path = self._dest_path()
        self.stage_button.setEnabled(False)
        self.staged_progress_bar.setVisible(True)
        self._stage_worker = GitStreamWorker(
            lambda on_output: self.git_service.stage_paths(dest_path, selected)
        )
        self._stage_worker.finished_ok.connect(self._on_stage_finished)
        self._stage_worker.failed.connect(self._on_stage_failed)
        self._stage_worker.start()

    def _on_stage_finished(self, _result: object) -> None:
        self.stage_button.setEnabled(True)
        self.staged_progress_bar.setVisible(False)
        self.refresh_status()

    def _on_stage_failed(self, message: str) -> None:
        self.stage_button.setEnabled(True)
        self.staged_progress_bar.setVisible(False)
        QMessageBox.warning(self, "Stage Failed", message)

    def _on_restore_clicked(self) -> None:
        selected = self._checked_paths(self.staged_list)
        if not selected or self._repo is None:
            return
        try:
            self.git_service.unstage_paths(self._dest_path(), selected)
        except GitOperationError as exc:
            QMessageBox.warning(self, "Restore Failed", str(exc))
            return
        self.refresh_status()

    def _show_inspect_menu(self, list_widget: QListWidget, pos) -> None:
        item = list_widget.itemAt(pos)
        if item is None or self._repo is None:
            return
        menu = QMenu(self)
        inspect_action = menu.addAction("Inspect in Explorer")
        action = menu.exec(list_widget.viewport().mapToGlobal(pos))
        if action == inspect_action:
            self.browse_file_requested.emit(self._dest_path() / item.text())

    def _on_revert_clicked(self) -> None:
        selected = self._checked_modified_paths()
        if not selected or self._repo is None:
            return
        confirmed = confirm_action(
            self,
            "Revert",
            f"Revert {len(selected)} selected file(s)? This discards their changes and cannot be undone.",
        )
        if not confirmed:
            return
        untracked = set(self._last_status.untracked) if self._last_status is not None else set()
        untracked_paths = [path for path in selected if path in untracked]
        modified_paths = [path for path in selected if path not in untracked]
        try:
            self.git_service.revert_paths(self._dest_path(), modified_paths=modified_paths, untracked_paths=untracked_paths)
        except GitOperationError as exc:
            QMessageBox.warning(self, "Revert Failed", str(exc))
            return
        self.refresh_status()

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
        self.progress_bar.setVisible(True)
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
                self.log_panel.append_line(f"--- Checking access to '{self._repo.name}' ---")
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
            self.progress_bar.setVisible(False)
            self.log_panel.append_line(f"--- Access denied to '{owner}/{name}' ---")
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
        self.log_panel.append_line(f"--- Syncing '{self._repo.name}' ---")
        self._git_worker = GitStreamWorker(
            lambda on_output: self.git_service.open_or_sync(self._repo.git_url, dest_path, on_output=on_output)
        )
        self._git_worker.output.connect(self.log_panel.append_line)
        self._git_worker.finished_ok.connect(self._on_sync_finished)
        self._git_worker.failed.connect(self._on_sync_failed)
        self._git_worker.start()

    def _on_sync_finished(self, status: str) -> None:
        self.sync_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        try:
            self.store.mark_synced(self._project.id, self._repo.id, "cloned")
        except UkoreHubError:
            pass
        self.log_panel.append_line(f"--- Done ({status}) ---")
        self.refresh_status()
        self.sync_finished.emit()

    def _on_sync_failed(self, message: str) -> None:
        self.sync_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        try:
            self.store.mark_status(self._project.id, self._repo.id, "error")
        except UkoreHubError:
            pass
        self.log_panel.append_line(f"--- Failed: {message} ---")
        QMessageBox.warning(self, "Sync Failed", message)
        self.sync_failed.emit(message)

    # -- commit -> pull -> (resolve conflicts) -> push -----------------------

    def _on_pull_and_push_clicked(self) -> None:
        if self._repo is None:
            return
        dialog = CommitDialog(self)
        if not dialog.exec():
            return
        self._pending_commit_message = dialog.message()
        self._pending_amend = dialog.amend()

        dest_path = self._dest_path()
        try:
            self.git_service.commit(
                dest_path,
                self._pending_commit_message,
                amend=self._pending_amend,
            )
        except GitOperationError as exc:
            QMessageBox.warning(self, "Commit Failed", str(exc))
            return
        self.log_panel.append_line("--- Committed ---")
        self._start_pull_step()

    def _set_workflow_running(self, running: bool) -> None:
        self.pull_push_button.setEnabled(not running)
        self.stage_button.setEnabled(not running)
        self.restore_button.setEnabled(not running)
        self.progress_bar.setVisible(running)

    def _start_pull_step(self) -> None:
        dest_path = self._dest_path()
        self.log_panel.append_line("--- Pulling ---")
        self._set_workflow_running(True)
        self._stream_worker = GitStreamWorker(
            lambda on_output: self.git_service.pull(dest_path, on_output=on_output)
        )
        self._stream_worker.output.connect(self.log_panel.append_line)
        self._stream_worker.finished_ok.connect(self._on_pull_step_finished)
        self._stream_worker.failed.connect(self._on_pull_step_failed)
        self._stream_worker.start()

    def _on_pull_step_finished(self) -> None:
        self.log_panel.append_line("--- Pull done ---")
        self._start_push_step()

    def _on_pull_step_failed(self, message: str) -> None:
        dest_path = self._dest_path()
        if not self.git_service.has_unresolved_merge(dest_path):
            self._set_workflow_running(False)
            self.log_panel.append_line(f"--- Pull failed: {message} ---")
            QMessageBox.warning(self, "Pull Failed", message)
            return
        self.log_panel.append_line("--- Merge conflict detected ---")
        conflicted = self.git_service.get_conflicted_files(dest_path)
        dialog = ConflictResolutionDialog(self, conflicted_files=conflicted)
        if not dialog.exec():
            self._set_workflow_running(False)
            self.log_panel.append_line("--- Conflicts left unresolved — resolve and try again ---")
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
        self.log_panel.append_line("--- Conflicts resolved, merge completed ---")
        self._start_push_step()

    def _start_push_step(self) -> None:
        dest_path = self._dest_path()
        self.log_panel.append_line("--- Pushing ---")
        self._stream_worker = GitStreamWorker(
            lambda on_output: self.git_service.push(dest_path, on_output=on_output)
        )
        self._stream_worker.output.connect(self.log_panel.append_line)
        self._stream_worker.finished_ok.connect(self._on_push_finished)
        self._stream_worker.failed.connect(self._on_push_failed)
        self._stream_worker.start()

    def _on_push_finished(self) -> None:
        self._set_workflow_running(False)
        self.log_panel.append_line("--- Push done ---")
        self.refresh_status()

    def _on_push_failed(self, message: str) -> None:
        self._set_workflow_running(False)
        self.log_panel.append_line(f"--- Push failed: {message} ---")
        QMessageBox.warning(self, "Push Failed", message)
