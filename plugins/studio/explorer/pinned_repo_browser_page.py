from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from core.exceptions import GitOperationError
from core.extensibility.file_opener import FileOpenerRegistry
from core.extensibility.hooks import GitHookContext
from core.git_service import GitService
from core.models import Project, Repo
from core.os_utils import open_with_default_app
from core.paths import resolve_repo_path
from interface.shared.widget_helpers import show_exclusive
from plugins.studio.explorer.browser_widget import RepoBrowserWidget


class _CloneWorker(QThread):
    """Runs GitService.clone() off the UI thread — same shape as
    path_commit_history_worker.py's PathCommitHistoryWorker, just for a
    clone instead of a commit-log fetch. output_received streams git's own
    --progress lines (see GitService._run_streaming) into the tab's log."""

    output_received = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(
        self, git_service: GitService, git_url: str, dest: Path, context: GitHookContext | None, parent=None
    ):
        super().__init__(parent)
        self._git_service = git_service
        self._git_url = git_url
        self._dest = dest
        self._context = context

    def run(self) -> None:
        try:
            self._git_service.clone(
                self._git_url, self._dest, on_output=self.output_received.emit, context=self._context
            )
        except GitOperationError as exc:
            self.failed.emit(str(exc))
            return
        self.finished_ok.emit()


class PinnedRepoBrowserPage(QWidget):
    """One dynamically-created top-level tab per Repo.explorer_pins entry —
    a full Explorer-style browser (the same RepoBrowserWidget the main
    Explorer tab uses) bound to a FIXED target repo, never the app's active
    repo. Rebuilt from scratch whenever the active repo (or its pins)
    change — see interface/main_window.py's _rebuild_pinned_explorer_tabs —
    so it doesn't need to react to set_repo() itself beyond accepting the
    call (same no-op convention interface/about/browser_link_page.py's
    BrowserLinkPage already uses for dynamic tabs)."""

    def __init__(
        self,
        parent=None,
        *,
        project: Project,
        repo: Repo,
        workspace_root: str,
        git_service: GitService,
        file_opener_registry: FileOpenerRegistry,
    ):
        super().__init__(parent)
        self._project = project
        self._repo = repo
        self._git_service = git_service
        self._file_opener_registry = file_opener_registry
        self._local_path = resolve_repo_path(workspace_root, project.name, repo.name)
        self._clone_worker: _CloneWorker | None = None

        self.not_cloned_label = QLabel(f"'{project.name} / {repo.name}' is not cloned locally yet.")
        self.clone_button = QPushButton("Clone")
        self.clone_button.clicked.connect(self._on_clone)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setVisible(False)
        self.log_view.setMaximumHeight(160)

        self.not_cloned_widget = QWidget()
        not_cloned_layout = QVBoxLayout(self.not_cloned_widget)
        not_cloned_layout.addWidget(self.not_cloned_label)
        not_cloned_layout.addWidget(self.clone_button)
        not_cloned_layout.addWidget(self.log_view)
        not_cloned_layout.addStretch()

        self.browser = RepoBrowserWidget(git_service=git_service, open_file=self._open_file)

        layout = QVBoxLayout(self)
        layout.addWidget(self.not_cloned_widget)
        layout.addWidget(self.browser)

        self._refresh_clone_state()

    def _open_file(self, path: Path) -> None:
        opener = self._file_opener_registry.find_opener(path, self._repo.enabled_addon_ids)
        if opener is not None and opener(path, self._repo):
            return
        open_with_default_app(path)

    def _refresh_clone_state(self) -> None:
        if (self._local_path / ".git").exists():
            show_exclusive(self.browser, self.not_cloned_widget)
            self.browser.set_root(self._local_path)
        else:
            show_exclusive(self.not_cloned_widget, self.browser)

    def _on_clone(self) -> None:
        if self._clone_worker is not None and self._clone_worker.isRunning():
            return
        self.clone_button.setEnabled(False)
        self.log_view.setVisible(True)
        self.log_view.clear()
        context = GitHookContext(project=self._project, repo=self._repo, repo_path=self._local_path)
        self._clone_worker = _CloneWorker(self._git_service, self._repo.git_url, self._local_path, context, self)
        self._clone_worker.output_received.connect(self.log_view.append)
        self._clone_worker.finished_ok.connect(self._on_clone_finished)
        self._clone_worker.failed.connect(self._on_clone_failed)
        self._clone_worker.start()

    def _on_clone_finished(self) -> None:
        self.clone_button.setEnabled(True)
        self._refresh_clone_state()

    def _on_clone_failed(self, message: str) -> None:
        self.clone_button.setEnabled(True)
        QMessageBox.warning(self, "Clone", f"Could not clone '{self._repo.name}':\n{message}")

    def background_threads(self) -> list:
        """Same shape as SectionSpec.background_threads (see plugin.py and
        interface/main_window.py's closeEvent) — the clone worker while a
        clone is in flight, plus the browser's own commit-history worker,
        so MainWindow can stop both safely on teardown/app-close instead of
        letting a running QThread get garbage-collected out from under it."""
        threads = [self.browser.commit_panel._worker]
        if self._clone_worker is not None:
            threads.append(self._clone_worker)
        return threads

    def set_repo(self, project: Project | None, repo: Repo | None, workspace_root: str | None) -> None:
        pass

    def browse_to_path(self, path: Path) -> None:
        pass
