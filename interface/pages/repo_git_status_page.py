from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
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

from core.exceptions import UkoreHubError
from core.git_service import GitService
from core.models import Project, Repo, RepoStatus
from core.paths import resolve_repo_path
from core.store import LocalConfigStore, MetadataStore
from interface.git_worker import GitWorker
from interface.log_panel import LogPanel
from interface.status_worker import RepoStatusWorker


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

        self.empty_label = QLabel("Select a repo to see this information.")

        self.commit_group = QGroupBox("Latest Commit")
        commit_form = QFormLayout(self.commit_group)
        self.commit_hash_label = QLabel("—")
        self.commit_author_label = QLabel("—")
        self.commit_date_label = QLabel("—")
        self.commit_message_label = QLabel("—")
        self.commit_message_label.setWordWrap(True)
        commit_form.addRow("Hash:", self.commit_hash_label)
        commit_form.addRow("Author:", self.commit_author_label)
        commit_form.addRow("Date:", self.commit_date_label)
        commit_form.addRow("Message:", self.commit_message_label)

        lists_row = QHBoxLayout()
        self.untracked_list = QListWidget()
        self.modified_list = QListWidget()
        self.staged_list = QListWidget()
        for title, widget in (
            ("Untracked", self.untracked_list),
            ("Modified", self.modified_list),
            ("Staged", self.staged_list),
        ):
            group = QGroupBox(title)
            group_layout = QVBoxLayout(group)
            group_layout.addWidget(widget)
            lists_row.addWidget(group)

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
        content_layout.addWidget(self.commit_group)
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

    def refresh_status(self) -> None:
        if self._repo is None or self._workspace_root is None:
            return
        dest_path = self._dest_path()
        if not (dest_path / ".git").exists():
            self.commit_hash_label.setText("—")
            self.commit_author_label.setText("—")
            self.commit_date_label.setText("—")
            self.commit_message_label.setText("Repo not yet cloned — click Sync.")
            self.untracked_list.clear()
            self.modified_list.clear()
            self.staged_list.clear()
            return
        self._status_worker = RepoStatusWorker(self.git_service, dest_path)
        self._status_worker.status_ready.connect(self._on_status_ready)
        self._status_worker.failed.connect(self._on_status_failed)
        self._status_worker.start()

    def _on_status_ready(self, status: RepoStatus) -> None:
        if status.commit is None:
            self.commit_hash_label.setText("—")
            self.commit_author_label.setText("—")
            self.commit_date_label.setText("—")
            self.commit_message_label.setText("No commits yet.")
        else:
            self.commit_hash_label.setText(status.commit.hash[:10])
            self.commit_author_label.setText(f"{status.commit.author} <{status.commit.email}>")
            self.commit_date_label.setText(status.commit.date)
            self.commit_message_label.setText(status.commit.message)
        self.untracked_list.clear()
        self.untracked_list.addItems(status.untracked)
        self.modified_list.clear()
        self.modified_list.addItems(status.modified)
        self.staged_list.clear()
        self.staged_list.addItems(status.staged)

    def _on_status_failed(self, message: str) -> None:
        self.log_panel.append_line(f"--- Failed to read status: {message} ---")

    def start_sync(self) -> None:
        if self._repo is None or self._workspace_root is None:
            return
        dest_path = self._dest_path()
        self.sync_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.log_panel.append_line(f"--- Syncing '{self._repo.name}' ---")
        self.sync_started.emit()

        self._git_worker = GitWorker(self.git_service, self._repo.git_url, dest_path)
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
