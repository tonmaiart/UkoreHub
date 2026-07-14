from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable

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
from interface.login.login_overlay import LoginOverlay
from interface.login.repo_picker import RepoPickerDialog
from interface.section_registry import SectionHost, SectionRegistry
from interface.settings.settings_view import SettingsView
from interface.settings_tab_registry import SettingsTabRegistry
from interface.sidebar.sidebar import Sidebar
from interface.web_engine_profile import make_persistent_browser_link_profile


# Explicit floor rather than a computed one (minimumSizeHint() right after
# setCentralWidget() is unreliable — layout isn't fully activated yet, and
# even once it is, widgets like the file table/list compress to a tiny
# hint, so doubling it barely moves) — and only a constraint on shrinking,
# not something that grows an already-taller window, so _build_main_ui()
# also force-resizes if the window is currently shorter than this.
MAIN_WINDOW_MIN_HEIGHT = 600


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
        self._login_overlay: LoginOverlay | None = None
        # The real main UI (sidebar + view_stack) is only ever constructed
        # once we know the user is logged in — see _build_main_ui(). Until
        # then these all stay at these empty/None defaults, and closeEvent()
        # guards on that (the window can still be closed while the login
        # gate is up, before any of this exists).
        self.pages: dict[str, QWidget] = {}
        self.sidebar: Sidebar | None = None
        self.view_stack: QStackedWidget | None = None
        self.settings_view: SettingsView | None = None
        self._section_view_index: dict[str, int] = {}
        self._settings_view_index: int | None = None
        self._dynamic_view_index: dict[str, int] = {}
        self._main_content: QWidget | None = None
        # Shared across every Browser Link tab so a login persists across
        # app restarts — see interface/web_engine_profile.py.
        self._web_engine_profile = make_persistent_browser_link_profile(
            self.store.json_path.parent / "webengine_profile", self
        )

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.show()

        # GitHub login is mandatory — the real main UI (sidebar, every
        # section's page, Settings) is never even constructed until we know
        # the user is logged in, so there's nothing for the login gate to
        # cover/hide: it's simply the central widget by itself first, then
        # _build_main_ui() replaces it once login succeeds. This avoids the
        # z-order/paint issues an always-on-top overlay had when drawn over
        # an already-built main UI.
        if self.local_config_store.github_username and self.token_store.load_token():
            self._build_main_ui()
            self._start_app_after_login()
        else:
            self._show_login_gate(self._on_initial_login_completed)

    # -- main UI construction (deferred until logged in) -------------------

    def _build_main_ui(self) -> None:
        section_registry = self.section_registry
        settings_tab_registry = self.settings_tab_registry

        # Built from the registry uniformly for built-in and plugin-provided
        # sections alike — built-in page_factories close over an
        # already-constructed singleton (see builtin_sections.py), a plugin's
        # factory constructs its page on this first (and only) call.
        self.pages = {spec.key: spec.page_factory() for spec in section_registry.ordered()}
        self.pages[builtin_sections.REPO_ABOUT].thumbnail_changed.connect(self._on_repo_thumbnail_changed)

        # Generic per-page wiring — lets a plugin page (Explorer, Submit)
        # connect its own signals to app-level services without MainWindow
        # importing that page's specific type. See
        # interface/section_registry.py's SectionHost/SectionSpec.wire.
        section_host = SectionHost(
            set_status_message=self._set_status_message,
            navigate_and_focus=self._navigate_and_focus,
        )
        for spec in section_registry.ordered():
            if spec.wire is not None:
                spec.wire(self.pages[spec.key], section_host)

        self.sidebar = Sidebar(section_registry=section_registry)
        self.sidebar.repo_picker_requested.connect(self._on_select_repo)
        self.sidebar.update_requested.connect(self._on_update_and_restart)
        self.sidebar.navigation_changed.connect(self._on_navigation_changed)
        self.sidebar.settings_requested.connect(self._on_settings_requested)

        # Every section is its own full-width top-level page, switched to via
        # the Sidebar's SectionTabList.
        self.view_stack = QStackedWidget()
        self._section_view_index = {
            spec.key: self.view_stack.addWidget(self.pages[spec.key]) for spec in section_registry.ordered()
        }

        self.settings_view = SettingsView(settings_tab_registry=settings_tab_registry)
        self._settings_view_index = self.view_stack.addWidget(self.settings_view)
        common_settings_page = self.settings_view.get_tab_widget(builtin_settings_tabs.COMMON)
        if common_settings_page is not None:
            common_settings_page.logout_requested.connect(self._on_logout_requested)
        browser_links_page = self.settings_view.get_tab_widget(builtin_settings_tabs.BROWSER_LINKS)
        if browser_links_page is not None:
            browser_links_page.browser_links_changed.connect(self._rebuild_browser_link_tabs)

        # One top-level tab + page per Browser Link on the active repo,
        # rebuilt from scratch on every repo switch and whenever Settings >
        # Repo > Browser changes — see _rebuild_browser_link_tabs.
        self._dynamic_view_index = {}

        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.sidebar)
        central_layout.addWidget(self.view_stack, stretch=1)
        self._main_content = central
        self.setCentralWidget(central)

        self.setMinimumHeight(MAIN_WINDOW_MIN_HEIGHT)
        if self.height() < MAIN_WINDOW_MIN_HEIGHT:
            self.resize(self.width(), MAIN_WINDOW_MIN_HEIGHT)

    # -- login gate ----------------------------------------------------

    def _show_login_gate(self, on_completed: Callable[[], None]) -> None:
        """Shows LoginOverlay as the central widget itself — replaces
        whatever was there (nothing yet on first launch; the real main UI,
        detached-but-kept-alive via takeCentralWidget(), on a relogin after
        logout — see _on_logout_requested) rather than being drawn on top of
        it, so there's no overlay/z-order fighting with already-built
        content."""
        self._login_overlay = LoginOverlay(
            self,
            system_config_store=self.system_config_store,
            local_config_store=self.local_config_store,
            token_store=self.token_store,
        )
        self._login_overlay.login_completed.connect(on_completed)
        self.setCentralWidget(self._login_overlay)

    def _teardown_login_gate(self) -> None:
        if self._login_overlay is not None:
            self.takeCentralWidget()
            self._login_overlay.deleteLater()
            self._login_overlay = None

    def _offer_repo_pick_after_login(self) -> None:
        # Auto-opens right after every successful login (first launch or a
        # relogin after logout) — same RepoPickerDialog used everywhere
        # else, just with its Cancel button relabeled "Skip" since there's
        # nothing being cancelled, just deferred.
        dialog = RepoPickerDialog(
            self,
            store=self.store,
            selected_project_id=self.local_config_store.active_project_id,
            selected_repo_id=self.local_config_store.active_repo_id,
            cancel_button_text="Skip",
        )
        if dialog.exec():
            self.local_config_store.set_active_repo(dialog.selected_project_id(), dialog.selected_repo_id())

    def _start_app_after_login(self) -> None:
        self._restore_active_repo()
        self._apply_to_current_page()
        self._restore_github_login_state()
        self._check_for_update()
        QTimer.singleShot(0, self._start_auto_sync)
        self._fire_app_started()

    def _on_initial_login_completed(self) -> None:
        self._teardown_login_gate()
        self._build_main_ui()
        self._offer_repo_pick_after_login()
        self._start_app_after_login()

    def _on_relogin_completed(self) -> None:
        self._teardown_login_gate()
        self.setCentralWidget(self._main_content)
        self._offer_repo_pick_after_login()
        self._restore_active_repo()
        self._apply_to_current_page()
        self._restore_github_login_state()
        self._start_auto_sync()

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

    def _set_status_message(self, message: str) -> None:
        self.sidebar.set_sync_message(message)

    def _navigate_and_focus(self, key: str, path: Path) -> None:
        # A page (e.g. Submit's "Inspect in Explorer") asking to jump to
        # another section and focus a specific file there — switches the
        # sidebar row + view stack to `key`, then calls that page's optional
        # browse_to_path(path) protocol method if it implements one (see
        # interface/section_registry.py's SectionHost).
        self.sidebar.tab_list.select(key)
        self._on_navigation_changed(key)
        page = self.pages.get(key)
        browse_to_path = getattr(page, "browse_to_path", None)
        if callable(browse_to_path):
            browse_to_path(path)

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
        self.settings_view.set_active_repo_name(repo.name)
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
        self.settings_view.set_active_repo_name(self._active_repo.name)
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
        without the user having to remember to sync manually. Calls the
        optional sync_active_repo(...) protocol method (see
        interface/section_registry.py's SectionHost) on whichever registered
        page(s) implement it — today, just Submit — rather than hardcoding
        a specific page type."""
        if self._active_repo is None or self._active_project is None:
            return
        workspace_root = self.local_config_store.workspace_root
        if not workspace_root:
            QMessageBox.information(
                self, "Select Repo", "Set a workspace folder in Setting > Common first."
            )
            return
        for page in self.pages.values():
            sync_active_repo = getattr(page, "sync_active_repo", None)
            if callable(sync_active_repo):
                sync_active_repo(self._active_project, self._active_repo, workspace_root)

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
        # gate shown at startup. Detach (not delete) the real main UI first,
        # so _on_relogin_completed can restore it as-is afterward instead of
        # rebuilding everything from scratch.
        self._main_content = self.takeCentralWidget()
        self._show_login_gate(self._on_relogin_completed)

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
        # know a section's internals. Guarded throughout since the window can
        # be closed before the main UI is even built (login gate still up).
        workers: list = [self._update_worker]
        if self.sidebar is not None:
            workers.append(self.sidebar.github_auth_widget._avatar_worker)
        if self.pages:
            for spec in self.section_registry.ordered():
                if spec.background_threads is not None:
                    workers.extend(spec.background_threads(self.pages[spec.key]))
        for thread in workers:
            if thread is not None and thread.isRunning():
                thread.terminate()
                thread.wait(3000)
        super().closeEvent(event)
