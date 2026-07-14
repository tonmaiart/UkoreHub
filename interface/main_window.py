from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QMessageBox, QStackedWidget, QWidget

from core import self_update
from core.exceptions import NotFoundError, UkoreHubError
from core.extensibility.hooks import GitHookContext, GitHookEvent, HookRegistry
from core.git_service import GitService
from core.github.token_store import TokenStore
from core.paths import resolve_repo_path
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
from core.version import APP_NAME, APP_VERSION
from interface import builtin_sections, builtin_settings_tabs
from interface.about.browser_link_page import BrowserLinkPage
from interface.login.launch_dialog import LaunchDialog
from interface.login.repo_picker import RepoPickerDialog
from interface.section_registry import SectionRegistry
from interface.settings.settings_view import SettingsView
from interface.settings_tab_registry import SettingsTabRegistry
from interface.sidebar.sidebar import Sidebar
from interface.web_engine_profile import make_persistent_browser_link_profile


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
        # Shared across every Browser Link tab so a login persists across
        # app restarts — see interface/web_engine_profile.py.
        self._web_engine_profile = make_persistent_browser_link_profile(
            self.store.json_path.parent / "webengine_profile", self
        )

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")

        # Built from the registry uniformly for built-in and plugin-provided
        # sections alike — built-in page_factories close over an
        # already-constructed singleton (see builtin_sections.py), a plugin's
        # factory constructs its page on this first (and only) call.
        self.pages = {spec.key: spec.page_factory() for spec in section_registry.ordered()}
        self.pages[builtin_sections.REPO_GIT_STATUS].sync_started.connect(self._on_sync_started)
        self.pages[builtin_sections.REPO_GIT_STATUS].sync_finished.connect(self._on_sync_finished)
        self.pages[builtin_sections.REPO_GIT_STATUS].sync_failed.connect(self._on_sync_failed)
        self.pages[builtin_sections.REPO_GIT_STATUS].browse_file_requested.connect(self._on_browse_file_requested)
        self.pages[builtin_sections.REPO_ABOUT].browser_links_changed.connect(self._rebuild_browser_link_tabs)
        self.pages[builtin_sections.REPO_ABOUT].thumbnail_changed.connect(self._on_repo_thumbnail_changed)

        self.sidebar = Sidebar(section_registry=section_registry)
        self.sidebar.repo_picker_requested.connect(self._on_select_repo)
        self.sidebar.update_requested.connect(self._on_update_and_restart)
        self.sidebar.navigation_changed.connect(self._on_navigation_changed)
        self.sidebar.settings_requested.connect(self._on_settings_requested)

        # Every section is its own full-width top-level page, switched to via
        # the Sidebar's SectionTabList.
        self.view_stack = QStackedWidget()
        self._section_view_index: dict[str, int] = {
            spec.key: self.view_stack.addWidget(self.pages[spec.key]) for spec in section_registry.ordered()
        }

        self.settings_view = SettingsView(settings_tab_registry=settings_tab_registry)
        self._settings_view_index = self.view_stack.addWidget(self.settings_view)
        common_settings_page = self.settings_view.get_tab_widget(builtin_settings_tabs.COMMON)
        if common_settings_page is not None:
            common_settings_page.logout_requested.connect(self._on_logout_requested)

        # One top-level tab + page per Browser Link on the active repo,
        # rebuilt from scratch on every repo switch and whenever About's
        # Browser Links section changes — see _rebuild_browser_link_tabs.
        self._dynamic_view_index: dict[str, int] = {}

        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.sidebar)
        central_layout.addWidget(self.view_stack, stretch=1)
        self.setCentralWidget(central)

        self.show()

        # GitHub login is mandatory — this blocks (re-showing the gate on
        # every rejected attempt) until the user is authenticated.
        self._ensure_logged_in()
        self._restore_active_repo()
        self._apply_to_current_page()

        self._restore_github_login_state()
        self._check_for_update()
        QTimer.singleShot(0, self._start_auto_sync)
        self._fire_app_started()

    def _ensure_logged_in(self) -> None:
        while not (self.local_config_store.github_username and self.token_store.load_token()):
            if not self._show_launch_dialog():
                # The mandatory login gate was closed without logging in —
                # LaunchDialog.reject() is supposed to prevent this, so this
                # is just a last-resort safety net: the app cannot run
                # unauthenticated.
                sys.exit(0)

    def _show_launch_dialog(self) -> bool:
        dialog = LaunchDialog(
            self,
            store=self.store,
            local_config_store=self.local_config_store,
            system_config_store=self.system_config_store,
            git_service=self.git_service,
            token_store=self.token_store,
        )
        return bool(dialog.exec())

    # -- navigation (Explorer / Submit / About / Setting / Browser Links) ---

    def _on_navigation_changed(self, key: str) -> None:
        index = self._section_view_index.get(key)
        if index is None:
            index = self._dynamic_view_index.get(key)
        if index is None:
            return
        self.view_stack.setCurrentIndex(index)
        self._apply_to_current_page()

    def _on_settings_requested(self) -> None:
        # Setting is its own icon button in Sidebar's footer now, not a row
        # in SectionTabList — deselect whatever section row was active so
        # the list doesn't keep showing a stale selection while Settings is
        # on screen (setCurrentRow(-1) doesn't fire navigation_changed, see
        # SectionTabList._on_current_row_changed's guard).
        self.sidebar.tab_list.setCurrentRow(-1)
        self.view_stack.setCurrentIndex(self._settings_view_index)
        self.settings_view.refresh_current_tab()

    def _on_browse_file_requested(self, path: Path) -> None:
        # "Browse" on a Submit-tab commit card / "Inspect in Explorer" on the
        # Modified or Staged list — jump to Explorer and show that file.
        self.sidebar.tab_list.select(builtin_sections.REPO_BROWSER)
        self._on_navigation_changed(builtin_sections.REPO_BROWSER)
        self.pages[builtin_sections.REPO_BROWSER].browser.browse_to_file(path)

    def _rebuild_browser_link_tabs(self) -> None:
        was_showing_dynamic = self.view_stack.currentIndex() in self._dynamic_view_index.values()
        # Resolve every widget by its (still-valid) index BEFORE removing
        # any of them — QStackedWidget re-indexes remaining widgets after
        # each removeWidget(), so removing by stale index one at a time
        # would skip/miss widgets once earlier removals shift things down.
        old_pages = [self.view_stack.widget(index) for index in self._dynamic_view_index.values()]
        for page in old_pages:
            self.view_stack.removeWidget(page)
            page.deleteLater()
        self._dynamic_view_index = {}
        self.sidebar.tab_list.clear_dynamic_tabs()

        if self._active_repo is not None:
            for link_index, link in enumerate(self._active_repo.browser_links):
                key = f"browser_link:{link_index}"
                view_index = self.view_stack.addWidget(BrowserLinkPage(link.url, self._web_engine_profile))
                self._dynamic_view_index[key] = view_index
                icon_path = self.store.resolve_browser_link_icon_path(link)
                self.sidebar.tab_list.add_dynamic_tab(key, link.name, icon_path)

        if was_showing_dynamic:
            # The tab the user was looking at just got torn down (its link
            # was removed, or the repo changed) — land on the first
            # remaining static section rather than hardcoding one.
            fallback_key = next(iter(self._section_view_index))
            self.sidebar.tab_list.select(fallback_key)
            self._on_navigation_changed(fallback_key)

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
        self.sidebar.active_repo_widget.set_active_labels(repo.name, project.name)
        self.sidebar.active_repo_widget.set_thumbnail(self.store.resolve_thumbnail_path(repo))
        self._rebuild_browser_link_tabs()

    def _on_repo_thumbnail_changed(self) -> None:
        # About > About's Choose Thumbnail always edits the currently active
        # repo (pages only ever get set_repo(active_project, active_repo, ...)
        # — see _apply_to_current_page), so this can refresh unconditionally.
        if self._active_repo is not None:
            self.sidebar.active_repo_widget.set_thumbnail(self.store.resolve_thumbnail_path(self._active_repo))

    def _current_page(self):
        if self.view_stack.currentIndex() == self._settings_view_index:
            return None
        return self.view_stack.currentWidget()

    def _apply_to_current_page(self) -> None:
        page = self._current_page()
        if page is not None:
            page.set_repo(self._active_project, self._active_repo, self.local_config_store.workspace_root)

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

    def _set_active_repo(self, project_id: str, repo_id: str) -> None:
        self.local_config_store.set_active_repo(project_id, repo_id)
        self._active_project = self.store.get_project(project_id)
        self._active_repo = self.store.get_repo(project_id, repo_id)
        self.sidebar.active_repo_widget.set_active_labels(self._active_repo.name, self._active_project.name)
        self.sidebar.active_repo_widget.set_thumbnail(self.store.resolve_thumbnail_path(self._active_repo))
        self._rebuild_browser_link_tabs()
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
        self.sidebar.set_sync_message(f"Syncing {self._active_repo.name}...")

    def _on_sync_finished(self) -> None:
        self.sidebar.set_sync_message("")

    def _on_sync_failed(self, _message: str) -> None:
        self.sidebar.set_sync_message("")

    # -- GitHub login -------------------------------------------------------

    def _restore_github_login_state(self) -> None:
        token = self.token_store.load_token()
        if self.local_config_store.github_username and token:
            self.sidebar.github_auth_widget.set_state(self.local_config_store.github_username)
            self.git_service.set_github_token(token)
        else:
            self.local_config_store.set_github_username(None)
            self.sidebar.github_auth_widget.set_state(None)
            self.git_service.set_github_token(None)

    def _on_logout_requested(self) -> None:
        self.token_store.clear_token()
        self.local_config_store.set_github_username(None)
        self.sidebar.github_auth_widget.set_state(None)
        self.git_service.set_github_token(None)
        # GitHub login is mandatory — logout goes straight back to the same
        # blocking gate shown at startup.
        self._ensure_logged_in()
        self._restore_github_login_state()

    # -- self-update --------------------------------------------------------

    def _check_for_update(self) -> None:
        self._update_worker = UpdateCheckWorker()
        self._update_worker.update_available.connect(self._on_update_check_result)
        self._update_worker.start()

    def _on_update_check_result(self, available: bool) -> None:
        self.sidebar.set_update_available(available)

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
        workers = [self._update_worker, self.sidebar.github_auth_widget._avatar_worker]
        for spec in self.section_registry.ordered():
            if spec.background_threads is not None:
                workers.extend(spec.background_threads(self.pages[spec.key]))
        for thread in workers:
            if thread is not None and thread.isRunning():
                thread.terminate()
                thread.wait(3000)
        super().closeEvent(event)
