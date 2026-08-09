from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from core.app_core import UkoreCore
from core.exceptions import NotFoundError
from core.events.hooks import AppLifecycleContext
from core.vcs.paths import resolve_repo_path
from core.relaunch import relaunch_ukorehub_exe
from core.version import APP_NAME, APP_VERSION
from interface import builtin_settings_tabs
from interface.page_protocols import AutoSyncPage, PathFocusablePage, SetRepoPage
from interface.section_registry import UICommandService
from interface.settings.settings_view import SettingsDialog
from interface.sidebar.sidebar import Sidebar
from interface.ui_registry_manager import UIRegistryManager

# interface/main_window.py -> interface/ -> repo root — used only to find
# UkoreHub.exe for _relaunch_to_login (the launcher exe built at the repo
# root by build_exe.py (UkoreHubLauncher repo)).
_REPO_ROOT = Path(__file__).resolve().parent.parent

# Explicit floor rather than a computed one (minimumSizeHint() right after
# setCentralWidget() is unreliable — layout isn't fully activated yet, and
# even once it is, widgets like the file table/list compress to a tiny
# hint, so doubling it barely moves) — and only a constraint on shrinking,
# not something that grows an already-taller window, so _build_main_ui()
# also force-resizes if the window is currently shorter than this.
MAIN_WINDOW_MIN_HEIGHT = 600


class MainWindow(QMainWindow):
    def __init__(
        self,
        core: UkoreCore,
        cache_dir: Path,
        registries: UIRegistryManager,
        section_key_to_plugin_id: dict[str, str] | None = None,
        core_plugin_ids: set[str] | None = None,
        opt_in_plugin_ids: set[str] | None = None,
    ):
        super().__init__()
        self._core = core
        self.store = core.metadata
        self.local_config_store = core.local_config
        self.git_service = core.git
        # Only used for logout (clearing the cached token) — login itself
        # happens entirely in the launcher exe now, see
        # updater.py (UkoreHubLauncher repo) and _on_logout_requested below.
        self._token_store = core.github_tokens
        self._cache_dir = Path(cache_dir)
        self.hook_registry = core.hooks
        self.section_registry = registries.sections
        self.settings_tab_registry = registries.settings_tabs
        self.file_opener_registry = registries.file_openers
        self.sidebar_footer_action_registry = registries.sidebar_footer_actions
        # Maps a SectionRegistry key back to the plugin id that registered
        # it (built in launcher.py by diffing section_registry.keys() around
        # each plugin's register(api) call) — used by _apply_plugin_visibility
        # to hide a disabled plugin's sidebar row for the active repo. Keys
        # with no entry here (e.g. the built-in "About" section) are never
        # gated, so at least one row always stays visible.
        self._section_key_to_plugin_id = section_key_to_plugin_id or {}
        # Plugin ids discovered under plugins/core/ (plugin_source() returns
        # "core" — see core.extensibility.loader) — their section always
        # stays visible in _apply_plugin_visibility, no per-repo opt-out
        # (see that method below). Built in launcher.py.
        self._core_plugin_ids = core_plugin_ids or set()
        # Plugin ids discovered under plugins/repo_internal/ or cache/plugins/
        # (plugin_source() returns "repo_internal"/"repo" — see
        # core.extensibility.loader) — gated opt-in per repo via
        # Repo.required_plugin_ids. repo_internal ships bundled with the
        # app like core; a "repo" plugin is its own separate git clone under
        # cache/plugins/ — different in kind, but the same "hidden until a
        # repo requires it" visibility rule applies to both. Built in
        # launcher.py.
        self._opt_in_plugin_ids = opt_in_plugin_ids or set()

        self._active_project = None
        self._active_repo = None
        self.pages: dict[str, QWidget] = {}
        self.sidebar: Sidebar | None = None
        self.view_stack: QStackedWidget | None = None
        self._section_view_index: dict[str, int] = {}

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")

        # No show()/showMaximized() call here on purpose — see
        # developer/bug-history/2026-07-20-main-window-not-maximizing.md. Nothing is
        # ever actually painted on screen until app.exec() starts running
        # the event loop, so building the whole widget tree first and only
        # then showing it, once, deferred via launcher.py's
        # QTimer.singleShot(0, window.showMaximized), is what makes the
        # window reliably come up maximized with no flash of a smaller
        # window first — a widget that's never been shown has no "size" for
        # the user to glimpse.
        #
        # GitHub login now happens in the launcher exe before this process
        # is even spawned (see updater.py (UkoreHubLauncher repo)) — by the time
        # MainWindow is constructed, GitService already has whatever token
        # was cached (see launcher.py's main()), so there's no in-app login
        # gate to show first.
        self._build_main_ui()
        self._start_app()

    # -- main UI construction -----------------------------------------------

    def _build_main_ui(self) -> None:
        section_registry = self.section_registry
        settings_tab_registry = self.settings_tab_registry

        # Built from the registry uniformly for built-in and plugin-provided
        # sections alike — a plugin's factory constructs its page on this
        # first (and only) call.
        self.pages = {spec.key: spec.page_factory() for spec in section_registry.ordered()}

        # Generic per-page wiring — lets a plugin page (Explorer, Submit)
        # connect its own signals to app-level services without MainWindow
        # importing that page's specific type. See
        # interface/section_registry.py's UICommandService/SectionSpec.wire.
        command_service = UICommandService(
            set_status_message=self._set_status_message,
            navigate_and_focus=self._navigate_and_focus,
            set_active_repo=self._set_active_repo,
            open_settings_tab=lambda key: self._on_settings_requested(select_key=key),
            switch_project=self._request_switch_project,
        )
        for spec in section_registry.ordered():
            if spec.wire is not None:
                spec.wire(self.pages[spec.key], command_service)

        self.sidebar = Sidebar(
            section_registry=section_registry, sidebar_footer_action_registry=self.sidebar_footer_action_registry
        )
        self.sidebar.navigation_changed.connect(self._on_navigation_changed)
        self.sidebar.external_link_activated.connect(self._on_external_link_activated)
        self.sidebar.settings_requested.connect(self._on_settings_requested)

        # Every section (including Project Editor, folded into this stack
        # like any other section as of this refactor — it used to be
        # SectionSpec.persistent=True, always visible docked beside
        # view_stack in a QSplitter rather than switched to) is its own
        # full-width top-level page, switched to via the Sidebar's
        # SectionTabList.
        self.view_stack = QStackedWidget()
        self._section_view_index = {
            spec.key: self.view_stack.addWidget(self.pages[spec.key]) for spec in section_registry.ordered()
        }

        # Setting is a popup dialog (SettingsDialog), not a view_stack page
        # — see _on_settings_requested, which constructs one fresh on every
        # open. A repo node's "Repository Setting..." right-click opens this
        # same dialog (via UICommandService.open_settings_tab) rather than a
        # popup of its own.

        # One dynamic Sidebar row per Browser Link on the active repo —
        # rebuilt from scratch on every repo switch and whenever it changes,
        # see _rebuild_dynamic_tabs. Opens externally on click (no
        # view_stack page of its own), so there's no view-index to track
        # here.

        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.sidebar)
        central_layout.addWidget(self.view_stack, stretch=1)
        self.setCentralWidget(central)

        self.setMinimumHeight(MAIN_WINDOW_MIN_HEIGHT)
        # This runs synchronously inside __init__ — safe to resize()
        # unconditionally here because, as of
        # developer/bug-history/2026-07-20-main-window-not-maximizing.md,
        # nothing ever calls show()/showMaximized() before this point
        # anymore (that's now deferred to launcher.py's single
        # QTimer.singleShot(0, window.showMaximized), after app.exec()
        # starts). The isMaximized() guard is kept anyway as defense in
        # depth — see that file's Lesson — in case a future change adds an
        # early show() call back and needs this to stay safe against it.
        if not self.isMaximized() and self.height() < MAIN_WINDOW_MIN_HEIGHT:
            self.resize(self.width(), MAIN_WINDOW_MIN_HEIGHT)

    def _start_app(self) -> None:
        self.sidebar.set_account_username(self.local_config_store.github_username)
        self._restore_active_repo()
        self._apply_to_current_page()
        QTimer.singleShot(0, self._start_auto_sync)
        self._fire_app_started()

    # -- navigation (Explorer / Submit / About / Setting / Browser Links) ---

    def _on_navigation_changed(self, key: str) -> None:
        index = self._section_view_index.get(key)
        if index is None:
            return
        self.view_stack.setCurrentIndex(index)
        self._apply_to_current_page()

    def _on_external_link_activated(self, url: str) -> None:
        """A Browser Link row (Sidebar.external_link_activated) — opens in
        the OS's default browser instead of an embedded page, see
        interface/sidebar/section_tab_list.py's class docstring."""
        QDesktopServices.openUrl(QUrl(url))

    def _on_settings_requested(self, select_key: str | None = None) -> None:
        # Setting is its own icon button in Sidebar's footer, opened as a
        # popup dialog (reverted 2026-07-19 from an embedded view_stack
        # page back to a dialog — see SettingsDialog's own docstring) —
        # whatever section is showing behind it stays exactly as it was,
        # so unlike the old view_stack-page version there's no sidebar row
        # to deselect here. select_key lets a section's own "Open Setting"
        # button (via UICommandService.open_settings_tab) land directly on one
        # tab instead of whatever opens by default — see
        # interface/section_registry.py's UICommandService.
        dialog = SettingsDialog(self, settings_tab_registry=self.settings_tab_registry)
        common_settings_page = dialog.view.get_tab_widget(builtin_settings_tabs.COMMON)
        if common_settings_page is not None:
            common_settings_page.logout_requested.connect(self._on_logout_requested)
            # Logging out closes the whole app (see _on_logout_requested) —
            # close the dialog itself too rather than leaving it floating
            # over nothing.
            common_settings_page.logout_requested.connect(dialog.accept)
            common_settings_page.restart_requested.connect(self._on_restart_requested)
        browser_links_page = dialog.view.get_tab_widget(builtin_settings_tabs.BROWSER_LINKS)
        if browser_links_page is not None:
            browser_links_page.browser_links_changed.connect(self._rebuild_dynamic_tabs)
        if select_key is not None:
            dialog.select_tab(select_key)
        dialog.exec()

    def _set_status_message(self, message: str) -> None:
        self.sidebar.set_sync_message(message)

    def _navigate_and_focus(self, key: str, path: Path) -> None:
        # A page (e.g. Submit's "Inspect in Explorer") asking to jump to
        # another section and focus a specific file there — switches the
        # sidebar row + view stack to `key`, then calls that page's optional
        # browse_to_path(path) protocol method if it implements one (see
        # interface/section_registry.py's UICommandService).
        self.sidebar.tab_list.select(key)
        self._on_navigation_changed(key)
        page = self.pages.get(key)
        if isinstance(page, PathFocusablePage):
            page.browse_to_path(path)

    def _rebuild_dynamic_tabs(self) -> None:
        """Rebuilds every dynamic (non-fixed) sidebar row — one per
        active-repo Browser Link. Called on every repo switch and whenever
        browser_links_changed fires. Each row just opens its link in the
        OS's default browser on click (see
        interface/sidebar/section_tab_list.py) rather than switching to an
        embedded view_stack page, so there's no page teardown or "was this
        the currently-showing page" fallback needed here anymore."""
        self.sidebar.tab_list.clear_dynamic_tabs()
        if self._active_repo is not None:
            for link_index, link in enumerate(self._active_repo.browser_links):
                key = f"browser_link:{link_index}"
                icon_path = self.store.resolve_browser_link_icon_path(link)
                self.sidebar.tab_list.add_dynamic_tab(key, link.name, icon_path, url=link.url)

    def _apply_plugin_visibility(self) -> None:
        """Hides the sidebar row of any plugins/ section the active repo
        doesn't currently want shown. A section with no entry in
        _section_key_to_plugin_id (e.g. the built-in "About" section) is
        never gated, so at least one row is always visible. Two different
        gating rules apply depending on where the section's plugin was
        discovered from (core.extensibility.loader.plugin_source):
        - plugins/core/ (self._core_plugin_ids) — always visible, no matter
          what (2026-08-04: no more per-repo opt-out here at all — anything
          repo-specific belongs under plugins/repo_internal/ instead, so
          plugins/core/ is meant to be universal app-level functionality,
          e.g. Project Editor, where switching the active repo has no other
          entry point).
        - plugins/repo_internal/ or cache/plugins/ (self._opt_in_plugin_ids,
          plugin_source() "repo_internal"/"repo") — opt-in: hidden unless the
          plugin id is in Repo.required_plugin_ids. A repo_internal plugin is
          bundled with the app like core but stays off until a repo declares
          it needed; a "repo" plugin is its own separate git clone under
          cache/plugins/ and is never on by default either. Same "off until
          required" shape as a Program requirement either way."""
        required_ids = self._active_repo.required_plugin_ids if self._active_repo is not None else []
        visible_keys = set()
        for key in self._section_view_index:
            plugin_id = self._section_key_to_plugin_id.get(key)
            if plugin_id is None or plugin_id in self._core_plugin_ids:
                visible_keys.add(key)
            elif plugin_id in self._opt_in_plugin_ids:
                if plugin_id in required_ids:
                    visible_keys.add(key)
        self.sidebar.tab_list.set_visible_keys(visible_keys)

        current_key = next(
            (key for key, index in self._section_view_index.items() if index == self.view_stack.currentIndex()),
            None,
        )
        if current_key is not None and current_key not in visible_keys:
            # Insertion-order (registry order) fallback, same
            # determinism as _rebuild_dynamic_tabs' own fallback.
            fallback_key = next(key for key in self._section_view_index if key in visible_keys)
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
        self._rebuild_dynamic_tabs()
        self._apply_plugin_visibility()

    def _current_page(self):
        # Setting is a popup dialog now (SettingsDialog), not a view_stack
        # page, so the current page is always a real section — no more
        # "is this actually Settings" special case needed here.
        return self.view_stack.currentWidget()

    def _apply_set_repo(self, page) -> None:
        # SetRepoPage is an optional per-page Protocol (interface/page_protocols.py),
        # same convention as _navigate_and_focus's PathFocusablePage above —
        # a page that has no notion of "active repo" (e.g. DebugConsole,
        # BananaSketch) simply doesn't implement it rather than being
        # forced into a no-op stub.
        if isinstance(page, SetRepoPage):
            page.set_repo(self._active_project, self._active_repo, self.local_config_store.workspace_root)

    def _apply_to_current_page(self) -> None:
        page = self._current_page()
        if page is not None:
            self._apply_set_repo(page)

    def _set_active_repo(self, project_id: str, repo_id: str) -> None:
        self.local_config_store.set_active_repo(project_id, repo_id)
        self._active_project = self.store.get_project(project_id)
        self._active_repo = self.store.get_repo(project_id, repo_id)
        self.sidebar.active_repo_widget.set_active_labels(self._active_repo.name, self._active_project.name)
        self.sidebar.active_repo_widget.set_thumbnail(self.store.resolve_thumbnail_path(self._active_repo))
        self._rebuild_dynamic_tabs()
        self._apply_plugin_visibility()
        self._apply_to_current_page()
        self._fire_repo_selected()
        self._start_auto_sync()

    def _fire_repo_selected(self) -> None:
        if not self.local_config_store.workspace_root:
            return
        repo_path = resolve_repo_path(
            self.local_config_store.workspace_root, self._active_project.name, self._active_repo.name
        )
        self.hook_registry.fire_repo_changed(
            AppLifecycleContext(project=self._active_project, repo=self._active_repo, repo_path=repo_path)
        )

    def _fire_app_started(self) -> None:
        workspace_root = self.local_config_store.workspace_root
        repo_path = Path(workspace_root) if workspace_root else Path.cwd()
        self.hook_registry.fire_app_start(
            AppLifecycleContext(project=self._active_project, repo=self._active_repo, repo_path=repo_path)
        )

    def _start_auto_sync(self) -> None:
        """Clone/pull the active repo. Runs on every "Select Repo..." pick and
        again on every app launch, so the working copy is always up to date
        without the user having to remember to sync manually. Calls the
        optional AutoSyncPage protocol method (interface/page_protocols.py)
        on whichever registered page(s) implement it — today, just Submit —
        rather than hardcoding a specific page type."""
        if self._active_repo is None or self._active_project is None:
            return
        workspace_root = self.local_config_store.workspace_root
        if not workspace_root:
            QMessageBox.information(
                self, "Select Repo", "Set a workspace folder in Setting > Common first."
            )
            return
        for page in self.pages.values():
            if isinstance(page, AutoSyncPage):
                page.sync_active_repo(self._active_project, self._active_repo, workspace_root)

    # -- GitHub logout ----------------------------------------------------

    def _on_logout_requested(self) -> None:
        # Login/token-caching moved entirely to the launcher exe (see
        # updater.py (UkoreHubLauncher repo)) — there's no in-app login gate to
        # send the user back to, so "logout" here means: clear the cached
        # token + username, then close this app and reopen the launcher
        # exe, whose own login step will show the GitHub login screen again
        # since the token is now gone.
        self._token_store.clear_token()
        self.local_config_store.set_github_username(None)
        self.local_config_store.set_github_login_at(None)
        self.sidebar.set_account_username(None)
        self._relaunch_to_login()

    @staticmethod
    def _relaunch_to_login() -> None:
        # relaunch_ukorehub_exe (core/relaunch.py) owns the _PYI_-env-var
        # stripping needed to avoid developer/bug-history/2026-08-04-
        # relaunch-inherits-pyinstaller-onefile-env.md — shared with
        # launcher.py's own mandatory login gate, see that module's
        # docstring.
        if not relaunch_ukorehub_exe(_REPO_ROOT):
            # Dev environment running via `python launcher.py` directly,
            # with no built exe next to it — there's no login UI left in
            # the plain-Python app to fall back to (see root README.md's
            # "Running" section), so just tell the user what to do.
            QMessageBox.information(
                None,
                "Logout",
                "Logged out. Run UkoreHub.exe to log back in.",
            )
        QApplication.quit()

    # -- restart --------------------------------------------------------------

    def _on_restart_requested(self) -> None:
        # Settings > Common's plain "Restart" button.
        self._restart_app()

    def _request_switch_project(self) -> None:
        # plugins/core/project_editor's Settings > Project "Switch
        # Project..." button, via UICommandService.switch_project. Project is
        # fixed for the whole run (LocalConfigStore.active_project_id, set
        # once by launcher.py's mandatory Project Selector gate before this
        # window was even built) — every page downstream assumed it
        # couldn't change under them, so the only honest way to view a
        # different one is the same real restart _on_logout_requested uses
        # for a changed identity, not an in-place swap. clear_active_repo()
        # resets both active_project_id and active_repo_id so the restarted
        # process's launcher.py gate sees nothing remembered and shows the
        # picker again instead of silently re-selecting this same project.
        self.local_config_store.clear_active_repo()
        self._restart_app()

    @staticmethod
    def _restart_app() -> None:
        os.execv(sys.executable, [sys.executable, *sys.argv])

    # -- shutdown -------------------------------------------------------------

    def closeEvent(self, event) -> None:
        workspace_root = self.local_config_store.workspace_root
        repo_path = Path(workspace_root) if workspace_root else Path.cwd()
        self.hook_registry.fire_app_close(
            AppLifecycleContext(project=self._active_project, repo=self._active_repo, repo_path=repo_path)
        )
        # Qt aborts the process if a QThread object is garbage-collected while
        # still running (e.g. an update check or sync in flight when the user
        # closes the window) — terminate and wait for any live worker first.
        # Built-in and plugin sections alike opt into this via
        # SectionSpec.background_threads, so main_window.py never needs to
        # know a section's internals.
        workers: list = []
        if self.sidebar is not None:
            for spec in self.sidebar_footer_action_registry.ordered():
                if spec.background_threads is not None:
                    workers.extend(spec.background_threads(self.sidebar.footer_action_widgets[spec.key]))
        if self.pages:
            for spec in self.section_registry.ordered():
                if spec.background_threads is not None:
                    workers.extend(spec.background_threads(self.pages[spec.key]))
        for thread in workers:
            if thread is not None and thread.isRunning():
                thread.terminate()
                thread.wait(3000)
        super().closeEvent(event)
