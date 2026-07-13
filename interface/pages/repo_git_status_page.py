from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import GitOperationError, UkoreHubError
from core.extensibility.hooks import GitHookContext
from core.git_service import GitService
from core.models import Project, Repo, RepoStatus
from core.paths import resolve_repo_path
from core.store import LocalConfigStore, MetadataStore
from interface.commit_dialog import CommitDialog
from interface.commit_log_worker import CommitLogWorker
from interface.conflict_dialog import ConflictResolutionDialog
from interface.git_stream_worker import GitStreamWorker
from interface.git_worker import GitWorker
from interface.log_panel import LogPanel
from interface.status_worker import RepoStatusWorker

COMMIT_LOG_PAGE_SIZE = 30


class RepoGitStatusPage(QWidget):
    sync_started = Signal()
    sync_finished = Signal()
    sync_failed = Signal(str)

    def __init__(self, parent=None, *, store: MetadataStore, local_config_store: LocalConfigStore, git_service: GitService):
        super().__init__(parent)
        self.store = store
        self.local_config_store = local_config_store
        self.git_service = git_service

        self._project: Project | None = None
        self._repo: Repo | None = None
        self._workspace_root: str | None = None
        self._git_worker: GitWorker | None = None
        self._status_worker: RepoStatusWorker | None = None
        self._stream_worker: GitStreamWorker | None = None
        self._commit_log_worker: CommitLogWorker | None = None
        self._commit_log_offset = 0
        self._pending_commit_message = ""
        self._pending_amend = False

        self.empty_label = QLabel("Select a repo to see this information.")

        self.commit_log_list = QListWidget()
        self.load_more_button = QPushButton("Load More")
        self.load_more_button.clicked.connect(lambda: self._load_commit_log(reset=False))
        commit_log_group = QGroupBox("Commit History")
        commit_log_layout = QVBoxLayout(commit_log_group)
        commit_log_layout.addWidget(self.commit_log_list)
        commit_log_layout.addWidget(self.load_more_button)

        lists_row = QHBoxLayout()

        self.modified_list = QListWidget()
        self.modified_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.stage_button = QPushButton("Stage")
        self.stage_button.clicked.connect(self._on_stage_clicked)
        modified_group = QGroupBox("Modified")
        modified_layout = QVBoxLayout(modified_group)
        modified_layout.addWidget(self.modified_list)
        modified_layout.addWidget(self.stage_button)
        lists_row.addWidget(modified_group)

        self.staged_list = QListWidget()
        self.staged_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.pull_push_button = QPushButton("Pull and Push")
        self.pull_push_button.clicked.connect(self._on_pull_and_push_clicked)
        staged_group = QGroupBox("Staged")
        staged_layout = QVBoxLayout(staged_group)
        staged_layout.addWidget(self.staged_list)
        staged_layout.addWidget(self.pull_push_button)
        lists_row.addWidget(staged_group)

        self.sync_button = QPushButton("Sync")
        self.sync_button.clicked.connect(self.start_sync)
        self.refresh_button = QPushButton("Refresh Status")
        self.refresh_button.clicked.connect(self.refresh_status)

        button_row = QHBoxLayout()
        button_row.addWidget(self.sync_button)
        button_row.addWidget(self.refresh_button)
        button_row.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)

        self.log_panel = LogPanel()

        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.addWidget(commit_log_group)
        content_layout.addLayout(lists_row)
        content_layout.addLayout(button_row)
        content_layout.addWidget(self.progress_bar)
        content_layout.addWidget(self.log_panel)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.content_widget)
        self.content_widget.setVisible(False)

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        self._project = project
        self._repo = repo
        self._workspace_root = workspace_root
        if repo is None:
            self.empty_label.setVisible(True)
            self.content_widget.setVisible(False)
            return
        self.empty_label.setVisible(False)
        self.content_widget.setVisible(True)
        self.refresh_status()

    def _dest_path(self):
        return resolve_repo_path(self._workspace_root, self._project.name, self._repo.name)

    def _hook_context(self, dest_path) -> GitHookContext:
        return GitHookContext(project=self._project, repo=self._repo, repo_path=dest_path)

    def refresh_status(self) -> None:
        if self._repo is None or self._workspace_root is None:
            return
        dest_path = self._dest_path()
        if not (dest_path / ".git").exists():
            self.commit_log_list.clear()
            self.commit_log_list.addItem("Repo not yet cloned — click Sync.")
            self.load_more_button.setEnabled(False)
            self.modified_list.clear()
            self.staged_list.clear()
            return
        self._load_commit_log(reset=True)
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
        self.modified_list.clear()
        self.modified_list.addItems(sorted(status.untracked + status.modified))
        self.staged_list.clear()
        self.staged_list.addItems(status.staged)

    def _on_status_failed(self, message: str) -> None:
        self.log_panel.append_line(f"--- Failed to read status: {message} ---")

    # -- commit log ---------------------------------------------------------

    def _load_commit_log(self, *, reset: bool) -> None:
        if self._repo is None or self._workspace_root is None:
            return
        if self._commit_log_worker is not None and self._commit_log_worker.isRunning():
            return
        if reset:
            self.commit_log_list.clear()
            self._commit_log_offset = 0
            self.load_more_button.setEnabled(True)
        dest_path = self._dest_path()
        self._commit_log_worker = CommitLogWorker(
            self.git_service, dest_path, self._commit_log_offset, COMMIT_LOG_PAGE_SIZE
        )
        self._commit_log_worker.log_ready.connect(self._on_commit_log_ready)
        self._commit_log_worker.start()

    def _on_commit_log_ready(self, commits: list) -> None:
        if not commits and self._commit_log_offset == 0:
            self.commit_log_list.addItem("No commits yet.")
        for commit in commits:
            self.commit_log_list.addItem(f"{commit.hash[:10]}  {commit.date}  {commit.author}: {commit.message}")
        self._commit_log_offset += len(commits)
        self.load_more_button.setEnabled(len(commits) == COMMIT_LOG_PAGE_SIZE)

    # -- stage ---------------------------------------------------------------

    def _on_stage_clicked(self) -> None:
        selected = [item.text() for item in self.modified_list.selectedItems()]
        if not selected or self._repo is None:
            return
        try:
            self.git_service.stage_paths(self._dest_path(), selected)
        except GitOperationError as exc:
            QMessageBox.warning(self, "Stage Failed", str(exc))
            return
        self.refresh_status()

    # -- sync (clone/pull, unchanged) ----------------------------------------

    def start_sync(self) -> None:
        if self._repo is None or self._workspace_root is None:
            return
        dest_path = self._dest_path()
        self.sync_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.log_panel.append_line(f"--- Syncing '{self._repo.name}' ---")
        self.sync_started.emit()

        self._git_worker = GitWorker(
            self.git_service, self._repo.git_url, dest_path, context=self._hook_context(dest_path)
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
                context=self._hook_context(dest_path),
            )
        except GitOperationError as exc:
            QMessageBox.warning(self, "Commit Failed", str(exc))
            return
        self.log_panel.append_line("--- Committed ---")
        self._start_pull_step()

    def _set_workflow_running(self, running: bool) -> None:
        self.pull_push_button.setEnabled(not running)
        self.stage_button.setEnabled(not running)
        self.progress_bar.setVisible(running)

    def _start_pull_step(self) -> None:
        dest_path = self._dest_path()
        self.log_panel.append_line("--- Pulling ---")
        self._set_workflow_running(True)
        self._stream_worker = GitStreamWorker(
            lambda on_output: self.git_service.pull(
                dest_path, on_output=on_output, context=self._hook_context(dest_path)
            )
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
            lambda on_output: self.git_service.push(
                dest_path, on_output=on_output, context=self._hook_context(dest_path)
            )
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
