from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from core import self_update
from core.exceptions import NotFoundError, UkoreHubError
from core.extensibility.hooks import GitHookContext, GitHookEvent, HookRegistry
from core.git_service import GitService
from core.github.token_store import TokenStore, TokenStoreFallbackUsed
from core.paths import resolve_repo_path
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
from core.version import APP_NAME, APP_VERSION
from interface import builtin_sections
from interface.github_login_dialog import GitHubLoginDialog
from interface.launch_dialog import LaunchDialog
from interface.menu_bar import MenuBar
from interface.repo_picker import RepoPickerDialog
from interface.section_registry import SectionRegistry
from interface.settings_tab_registry import SettingsTabRegistry
from interface.settings_view import SettingsView
from interface.sidebar import Sidebar
from interface.top_tab_bar import TopTabBar


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
        program_store: ProgramStore,
        git_service: GitService,
        token_store: TokenStore,
        hook_registry: HookRegistry,
        section_registry: SectionRegistry,
        settings_tab_registry: SettingsTabRegistry,
    ):
        super().__init__()
        self.store = store
        self.local_config_store = local_config_store
        self.system_config_store = system_config_store
        self.program_store = program_store
        self.git_service = git_service
        self.token_store = token_store
        self.hook_registry = hook_registry
        self.section_registry = section_registry
        self.settings_tab_registry = settings_tab_registry

        self._active_project = None
        self._active_repo = None
        self._update_worker: UpdateCheckWorker | None = None
        self._login_dialog: GitHubLoginDialog | None = None

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")

        self.sidebar = Sidebar()
        self.sidebar.repo_picker_requested.connect(self._on_select_repo)
        self.sidebar.combo_repo_selected.connect(self._on_combo_repo_selected)

        # Built from the registry uniformly for built-in and plugin-provided
        # sections alike — built-in page_factories close over an
        # already-constructed singleton (see builtin_sections.py), a plugin's
        # factory constructs its page on this first (and only) call.
        self.pages = {spec.key: spec.page_factory() for spec in section_registry.ordered()}
        self.pages[builtin_sections.REPO_GIT_STATUS].sync_started.connect(self._on_sync_started)
        self.pages[builtin_sections.REPO_GIT_STATUS].sync_finished.connect(self._on_sync_finished)
        self.pages[builtin_sections.REPO_GIT_STATUS].sync_failed.connect(self._on_sync_failed)

        # Sidebar-backed sections (Repo/About) share one content_stack next to
        # the sidebar; standalone sections (Explorer/Submit) get their own
        # full-width page directly in view_stack, no sidebar — see
        # SectionSpec.standalone.
        ordered_specs = section_registry.ordered()
        sidebar_specs = [spec for spec in ordered_specs if not spec.standalone]
        standalone_specs = [spec for spec in ordered_specs if spec.standalone]

        self.content_stack = QStackedWidget()
        self._section_order = [spec.key for spec in sidebar_specs]
        for key in self._section_order:
            self.content_stack.addWidget(self.pages[key])
        self.content_stack.currentChanged.connect(self._on_stack_current_changed)

        self.tab_bar = TopTabBar(section_registry=section_registry)
        self.tab_bar.tab_changed.connect(self._on_tab_changed)

        self.menu_bar = MenuBar(tab_bar=self.tab_bar)
        self.menu_bar.login_requested.connect(self._on_login_requested)
        self.menu_bar.logout_requested.connect(self._on_logout_requested)
        self.menu_bar.update_requested.connect(self._on_update_and_restart)
        self.menu_bar.settings_requested.connect(self._on_settings_requested)

        repo_view = QWidget()
        repo_view_layout = QHBoxLayout(repo_view)
        repo_view_layout.setContentsMargins(0, 0, 0, 0)
        repo_view_layout.setSpacing(0)
        repo_view_layout.addWidget(self.sidebar)
        repo_view_layout.addWidget(self.content_stack, stretch=1)

        self.settings_view = SettingsView(settings_tab_registry=settings_tab_registry)

        self.view_stack = QStackedWidget()
        self._repo_view_index = self.view_stack.addWidget(repo_view)
        self._standalone_view_index = {
            spec.key: self.view_stack.addWidget(self.pages[spec.key]) for spec in standalone_specs
        }
        self._settings_view_index = self.view_stack.addWidget(self.settings_view)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.menu_bar)
        central_layout.addWidget(self.view_stack, stretch=1)
        self.setCentralWidget(central)

        self.resize(1100, 700)

        self._restore_active_repo()
        self._apply_to_current_page()
        self.sidebar.refresh_repo_choices(self.store)

        if not (self.local_config_store.github_username and self.token_store.load_token()):
            self._show_launch_dialog()
            # LaunchDialog may have changed active repo or login state —
            # re-sync everything it could have touched.
            self._restore_active_repo()
            self._apply_to_current_page()
            self.sidebar.refresh_repo_choices(self.store)

        self._restore_github_login_state()
        self._check_for_update()
        QTimer.singleShot(0, self._start_auto_sync)
        self._fire_app_started()

    def _show_launch_dialog(self) -> None:
        dialog = LaunchDialog(
            self,
            store=self.store,
            local_config_store=self.local_config_store,
            system_config_store=self.system_config_store,
            git_service=self.git_service,
            token_store=self.token_store,
        )
        dialog.exec()

    # -- top tab switching (Repo / Explorer / Submit / About / Setting) -----

    def _on_tab_changed(self, key: str) -> None:
        # TopTabBar and the Setting button are deliberately two separate
        # exclusive groups (Setting isn't repo-scoped) — keep them visually
        # in sync by hand instead.
        self.menu_bar.setting_button.setChecked(False)
        if key in self._standalone_view_index:
            self.view_stack.setCurrentIndex(self._standalone_view_index[key])
        else:
            was_setting = self.view_stack.currentIndex() == self._settings_view_index
            self.view_stack.setCurrentIndex(self._repo_view_index)
            self.content_stack.setCurrentIndex(self._section_order.index(key))
            if was_setting:
                # Mirrors what used to run right after the modal Settings
                # dialog closed — there's no single "closed" moment anymore,
                # so this runs every time the user switches back from
                # Setting instead.
                self.sidebar.refresh_repo_choices(self.store)
                if self._active_repo is not None:
                    self.sidebar.set_thumbnail(self.store.resolve_thumbnail_path(self._active_repo))
        self._apply_to_current_page()

    def _on_settings_requested(self) -> None:
        self.tab_bar.uncheck_all()
        self.menu_bar.setting_button.setChecked(True)
        self.view_stack.setCurrentIndex(self._settings_view_index)
        self.settings_view.refresh_current_tab()

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

    def _current_page(self):
        index = self.view_stack.currentIndex()
        if index == self._settings_view_index:
            return None
        if index == self._repo_view_index:
            return self.content_stack.currentWidget()
        return self.view_stack.currentWidget()  # a standalone section's page

    def _apply_to_current_page(self) -> None:
        page = self._current_page()
        if page is not None:
            page.set_repo(self._active_project, self._active_repo, self.local_config_store.workspace_root)

    def _on_stack_current_changed(self, _index: int) -> None:
        self._apply_to_current_page()

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
        self._fire_repo_selected()
        self._start_auto_sync()

    def _fire_repo_selected(self) -> None:
        if not self.local_config_store.workspace_root:
            return
        repo_path = resolve_repo_path(
            self.local_config_store.workspace_root, self._active_project.name, self._active_repo.name
        )
        self.hook_registry.fire(
            GitHookEvent.REPO_SELECTED,
            GitHookContext(project=self._active_project, repo=self._active_repo, repo_path=repo_path),
        )

    def _fire_app_started(self) -> None:
        workspace_root = self.local_config_store.workspace_root
        repo_path = Path(workspace_root) if workspace_root else Path.cwd()
        self.hook_registry.fire(
            GitHookEvent.APP_STARTED,
            GitHookContext(project=self._active_project, repo=self._active_repo, repo_path=repo_path),
        )

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
        git_status_page = self.pages[builtin_sections.REPO_GIT_STATUS]
        git_status_page.set_repo(self._active_project, self._active_repo, workspace_root)
        git_status_page.start_sync()

    def _on_sync_started(self) -> None:
        self.menu_bar.set_sync_message(f"Syncing {self._active_repo.name}...")

    def _on_sync_finished(self) -> None:
        self.menu_bar.set_sync_message("")
        self.sidebar.refresh_repo_choices(self.store)

    def _on_sync_failed(self, _message: str) -> None:
        self.menu_bar.set_sync_message("")

    # -- GitHub login -------------------------------------------------------

    def _restore_github_login_state(self) -> None:
        token = self.token_store.load_token()
        if self.local_config_store.github_username and token:
            self.menu_bar.github_auth_widget.set_state(self.local_config_store.github_username)
            self.git_service.set_github_token(token)
        else:
            self.local_config_store.set_github_username(None)
            self.menu_bar.github_auth_widget.set_state(None)
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
            self.menu_bar.github_auth_widget.set_state(username)
            self.git_service.set_github_token(token)

    def _on_logout_requested(self) -> None:
        self.token_store.clear_token()
        self.local_config_store.set_github_username(None)
        self.menu_bar.github_auth_widget.set_state(None)
        self.git_service.set_github_token(None)

    # -- self-update --------------------------------------------------------

    def _check_for_update(self) -> None:
        self._update_worker = UpdateCheckWorker()
        self._update_worker.update_available.connect(self._on_update_check_result)
        self._update_worker.start()

    def _on_update_check_result(self, available: bool) -> None:
        self.menu_bar.set_update_available(available)

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
        # Built-in and plugin sections alike opt into this via
        # SectionSpec.background_threads, so main_window.py never needs to
        # know a section's internals.
        workers = [self._update_worker, self.menu_bar.github_auth_widget._avatar_worker]
        for spec in self.section_registry.ordered():
            if spec.background_threads is not None:
                workers.extend(spec.background_threads(self.pages[spec.key]))
        for thread in workers:
            if thread is not None and thread.isRunning():
                thread.terminate()
                thread.wait(3000)
        super().closeEvent(event)
