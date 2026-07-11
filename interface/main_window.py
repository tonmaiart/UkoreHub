from __future__ import annotations

import os
import sys

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QWidget,
)

from core import self_update
from core.exceptions import NotFoundError, UkoreHubError
from core.git_service import GitService
from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
from core.token_store import TokenStore, TokenStoreFallbackUsed
from core.version import APP_NAME, APP_VERSION
from interface.github_auth_widget import GitHubAuthWidget
from interface.github_login_dialog import GitHubLoginDialog
from interface.pages.project_info_page import ProjectInfoPage
from interface.pages.repo_about_page import RepoAboutPage
from interface.pages.repo_browser_page import RepoBrowserPage
from interface.pages.repo_git_status_page import RepoGitStatusPage
from interface.repo_picker import RepoPickerDialog
from interface.section_keys import SectionKey
from interface.settings_dialog import SettingsDialog
from interface.sidebar import Sidebar


class UpdateCheckWorker(QThread):
    update_available = Signal(bool)

    def run(self) -> None:
        try:
            available = self_update.check_for_update()
        except UkoreHubError:
            available = False
        self.update_available.emit(available)


class MainWindow(QMainWindow):
    def __init__(
        self,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        system_config_store: SystemConfigStore,
        git_service: GitService,
        token_store: TokenStore,
    ):
        super().__init__()
        self.store = store
        self.local_config_store = local_config_store
        self.system_config_store = system_config_store
        self.git_service = git_service
        self.token_store = token_store

        self._active_project = None
        self._active_repo = None
        self._update_worker: UpdateCheckWorker | None = None
        self._login_dialog: GitHubLoginDialog | None = None

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")

        self.sidebar = Sidebar()
        self.sidebar.repo_picker_requested.connect(self._on_select_repo)
        self.sidebar.section_changed.connect(self._on_section_changed)
        self.sidebar.combo_repo_selected.connect(self._on_combo_repo_selected)

        self.pages = {
            SectionKey.PROJECT_INFO: ProjectInfoPage(store=store, local_config_store=local_config_store, git_service=git_service),
            SectionKey.REPO_BROWSER: RepoBrowserPage(store=store, local_config_store=local_config_store, git_service=git_service),
            SectionKey.REPO_GIT_STATUS: RepoGitStatusPage(store=store, local_config_store=local_config_store, git_service=git_service),
            SectionKey.REPO_ABOUT: RepoAboutPage(store=store, local_config_store=local_config_store, git_service=git_service),
        }
        self.pages[SectionKey.REPO_GIT_STATUS].sync_started.connect(self._on_sync_started)
        self.pages[SectionKey.REPO_GIT_STATUS].sync_finished.connect(self._on_sync_finished)
        self.pages[SectionKey.REPO_GIT_STATUS].sync_failed.connect(self._on_sync_failed)

        self.content_stack = QStackedWidget()
        self._section_order = list(SectionKey)
        for section in self._section_order:
            self.content_stack.addWidget(self.pages[section])
        self.content_stack.currentChanged.connect(self._on_stack_current_changed)

        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.sidebar)
        central_layout.addWidget(self.content_stack, stretch=1)
        self.setCentralWidget(central)

        self._build_status_bar()
        self.resize(1100, 700)

        self._restore_active_repo()
        self._apply_to_current_page()
        self.sidebar.refresh_repo_choices(self.store)
        self._restore_github_login_state()
        self._check_for_update()
        QTimer.singleShot(0, self._start_auto_sync)

    def _build_status_bar(self) -> None:
        status_bar = self.statusBar()

        self.app_label = QLabel(f"{APP_NAME} {APP_VERSION}")
        status_bar.addWidget(self.app_label)

        self.update_button = QPushButton("Update and Restart")
        self.update_button.clicked.connect(self._on_update_and_restart)
        self.update_button.setVisible(False)
        status_bar.addWidget(self.update_button)

        self.sync_progress_bar = QProgressBar()
        self.sync_progress_bar.setRange(0, 0)
        self.sync_progress_bar.setFixedWidth(120)
        self.sync_progress_bar.setVisible(False)
        status_bar.addPermanentWidget(self.sync_progress_bar)

        self.github_auth_widget = GitHubAuthWidget()
        self.github_auth_widget.login_requested.connect(self._on_login_requested)
        self.github_auth_widget.logout_requested.connect(self._on_logout_requested)
        status_bar.addPermanentWidget(self.github_auth_widget)

        self.settings_button = QPushButton("Setting")
        self.settings_button.clicked.connect(self._on_open_settings)
        status_bar.addPermanentWidget(self.settings_button)

    # -- active repo -----------------------------------------------------

    def _restore_active_repo(self) -> None:
        project_id = self.local_config_store.active_project_id
        repo_id = self.local_config_store.active_repo_id
        if not project_id or not repo_id:
            return
        try:
            project = self.store.get_project(project_id)
            repo = self.store.get_repo(project_id, repo_id)
        except NotFoundError:
            self.local_config_store.clear_active_repo()
            return
        self._active_project = project
        self._active_repo = repo
        self.sidebar.set_active_labels(project.name, repo.name)
        self.sidebar.set_thumbnail(self.store.resolve_thumbnail_path(repo))

    def _apply_to_current_page(self) -> None:
        page = self.content_stack.currentWidget()
        if page is not None:
            page.set_repo(self._active_project, self._active_repo, self.local_config_store.workspace_root)

    def _on_stack_current_changed(self, _index: int) -> None:
        self._apply_to_current_page()

    def _on_section_changed(self, section: SectionKey) -> None:
        index = self._section_order.index(section)
        self.content_stack.setCurrentIndex(index)

    def _on_select_repo(self) -> None:
        dialog = RepoPickerDialog(
            self,
            store=self.store,
            selected_project_id=self._active_project.id if self._active_project else None,
            selected_repo_id=self._active_repo.id if self._active_repo else None,
        )
        if not dialog.exec():
            return
        self._set_active_repo(dialog.selected_project_id(), dialog.selected_repo_id())

    def _on_combo_repo_selected(self, project_id: str, repo_id: str) -> None:
        self._set_active_repo(project_id, repo_id)

    def _set_active_repo(self, project_id: str, repo_id: str) -> None:
        self.local_config_store.set_active_repo(project_id, repo_id)
        self._active_project = self.store.get_project(project_id)
        self._active_repo = self.store.get_repo(project_id, repo_id)
        self.sidebar.set_active_labels(self._active_project.name, self._active_repo.name)
        self.sidebar.set_thumbnail(self.store.resolve_thumbnail_path(self._active_repo))
        self._apply_to_current_page()
        self._start_auto_sync()

    def _start_auto_sync(self) -> None:
        """Clone/pull the active repo. Runs on every "Select Repo..." pick and
        again on every app launch, so the working copy is always up to date
        without the user having to remember to sync manually."""
        if self._active_repo is None or self._active_project is None:
            return
        workspace_root = self.local_config_store.workspace_root
        if not workspace_root:
            QMessageBox.information(
                self, "Select Repo", "Set a workspace folder in Setting > Common first."
            )
            return
        git_status_page = self.pages[SectionKey.REPO_GIT_STATUS]
        git_status_page.set_repo(self._active_project, self._active_repo, workspace_root)
        git_status_page.start_sync()

    def _on_sync_started(self) -> None:
        self.statusBar().showMessage(f"Syncing {self._active_repo.name}...")
        self.sync_progress_bar.setVisible(True)

    def _on_sync_finished(self) -> None:
        self.statusBar().clearMessage()
        self.sync_progress_bar.setVisible(False)
        self.sidebar.refresh_repo_choices(self.store)

    def _on_sync_failed(self, _message: str) -> None:
        self.statusBar().clearMessage()
        self.sync_progress_bar.setVisible(False)

    # -- settings ---------------------------------------------------------

    def _on_open_settings(self) -> None:
        dialog = SettingsDialog(
            self,
            store=self.store,
            local_config_store=self.local_config_store,
            system_config_store=self.system_config_store,
            git_service=self.git_service,
        )
        dialog.exec()
        self._apply_to_current_page()
        self.sidebar.refresh_repo_choices(self.store)
        if self._active_repo is not None:
            self.sidebar.set_thumbnail(self.store.resolve_thumbnail_path(self._active_repo))

    # -- GitHub login -------------------------------------------------------

    def _restore_github_login_state(self) -> None:
        token = self.token_store.load_token()
        if self.local_config_store.github_username and token:
            self.github_auth_widget.set_state(self.local_config_store.github_username)
            self.git_service.set_github_token(token)
        else:
            self.local_config_store.set_github_username(None)
            self.github_auth_widget.set_state(None)
            self.git_service.set_github_token(None)

    def _on_login_requested(self) -> None:
        if not self.system_config_store.github_client_id:
            QMessageBox.information(
                self,
                "GitHub Login",
                "No GitHub OAuth Client ID configured yet.\n\n"
                "Register a public OAuth App at github.com/settings/developers "
                "(enable \"Device Flow\"), then paste its Client ID into "
                "Setting > Common.",
            )
            return
        self._login_dialog = GitHubLoginDialog(self, client_id=self.system_config_store.github_client_id)
        if self._login_dialog.exec():
            username = self._login_dialog.username
            token = self._login_dialog.token
            try:
                self.token_store.save_token(token)
            except TokenStoreFallbackUsed as exc:
                QMessageBox.warning(self, "GitHub Login", str(exc))
            self.local_config_store.set_github_username(username)
            self.github_auth_widget.set_state(username)
            self.git_service.set_github_token(token)

    def _on_logout_requested(self) -> None:
        self.token_store.clear_token()
        self.local_config_store.set_github_username(None)
        self.github_auth_widget.set_state(None)
        self.git_service.set_github_token(None)

    # -- self-update --------------------------------------------------------

    def _check_for_update(self) -> None:
        self._update_worker = UpdateCheckWorker()
        self._update_worker.update_available.connect(self._on_update_check_result)
        self._update_worker.start()

    def _on_update_check_result(self, available: bool) -> None:
        self.update_button.setVisible(available)

    def _on_update_and_restart(self) -> None:
        try:
            self_update.pull_update()
        except UkoreHubError as exc:
            QMessageBox.warning(self, "Update Failed", str(exc))
            return
        os.execv(sys.executable, [sys.executable, *sys.argv])

    # -- shutdown -------------------------------------------------------------

    def closeEvent(self, event) -> None:
        # Qt aborts the process if a QThread object is garbage-collected while
        # still running (e.g. an update check or sync in flight when the user
        # closes the window) — terminate and wait for any live worker first.
        git_status_page = self.pages[SectionKey.REPO_GIT_STATUS]
        workers = (
            self._update_worker,
            git_status_page._git_worker,
            git_status_page._status_worker,
            git_status_page._stream_worker,
            git_status_page._commit_log_worker,
        )
        for thread in workers:
            if thread is not None and thread.isRunning():
                thread.terminate()
                thread.wait(3000)
        super().closeEvent(event)
