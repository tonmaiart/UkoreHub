from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import QFile, QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QWidget,
)

from core_api import APP_NAME, APP_VERSION, AppLifecycleContext, NotFoundError, UkoreCore, relaunch_ukorehub_exe
from interface import builtin_settings_tabs
from interface.page_protocols import PathFocusablePage, RefreshablePage, SetRepoPage
from interface.settings.settings_view import SettingsDialog
from interface.sidebar.section_tab_list import SectionTabList
from plugin_api import UICommandService, UIRegistryManager

import subprocess

# interface/main_window.py -> interface/ -> repo root — used only to find
# UkoreHub.exe for _relaunch_to_login (the launcher exe built at the repo
# root by build_exe.py (UkoreHubLauncher repo)).
_REPO_ROOT = Path(__file__).resolve().parent.parent

# Sidebar + view_stack shell, authored in Qt Designer and loaded at runtime
# instead of being built widget-by-widget in code — same QUiLoader pattern
# interface/repo_settings/requirements_and_plugins_page.py uses for
# RepoSettingWindow.ui. Authored by hand in Designer (MainWindow.ui, not
# main_window.py's own naming convention — keep the exact on-disk casing).
# Sidebar used to be its own Sidebar(QWidget) class
# (interface/sidebar/sidebar.py, removed) and the repo thumbnail/name used
# to be ActiveRepoWidget (interface/sidebar/active_repo_widget.py, also
# removed) — MainWindow now owns every widget directly, found by
# objectName off the loaded .ui.
_UI_FILE = Path(__file__).parent / "MainWindow.ui"

# Fallback size for the repo thumbnail crop (_set_thumbnail) when
# label_thumbnail hasn't been laid out yet (still 0x0 the first time a repo
# is restored, since that runs before the window is ever shown/activated).
_THUMBNAIL_FALLBACK_SIZE = QSize(230, 140)

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
        self.notification_registry = registries.notifications
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
        # Plugin ids discovered under cache/plugins/ (plugin_source() returns
        # "repo" — see core.extensibility.loader) — gated opt-in per repo via
        # Repo.required_plugin_ids. Each entry is its own separate git clone,
        # never on by default. Built in launcher.py.
        self._opt_in_plugin_ids = opt_in_plugin_ids or set()

        self._active_project = None
        self._active_repo = None
        self.pages: dict[str, QWidget] = {}
        self.thumbnail_label: QLabel | None = None
        self.repo_name_label: QLabel | None = None
        self._thumbnail_source_pixmap: QPixmap | None = None
        self.tab_list: SectionTabList | None = None
        self.setting_button: QPushButton | None = None
        # One widget per SidebarFooterActionRegistry entry, keyed by
        # spec.key — so closeEvent can reach a plugin's own
        # background_threads without knowing what they are.
        self.footer_action_widgets: dict[str, QWidget] = {}
        # One widget per NotificationRegistry entry, keyed by spec.key —
        # same closeEvent-cleanup purpose as footer_action_widgets above.
        self.notification_widgets: dict[str, QWidget] = {}
        self.notification_list: QListWidget | None = None
        self.view_stack: QStackedWidget | None = None
        self._section_view_index: dict[str, int] = {}

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")

        # No show()/showMaximized() call here on purpose — see the
        # ukorehub-interface skill. Nothing is ever actually painted on
        # screen until app.exec() starts running
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
        # plugin_api/registries/section_registry.py's UICommandService/SectionSpec.wire.
        command_service = UICommandService(
            set_status_message=self._set_status_message,
            navigate_and_focus=self._navigate_and_focus,
            set_active_repo=self._set_active_repo,
            open_settings_tab=lambda key: self._on_settings_requested(select_key=key),
            switch_project=self._request_switch_project,
            refresh_section=self._refresh_section,
        )
        for spec in section_registry.ordered():
            if spec.wire is not None:
                spec.wire(self.pages[spec.key], command_service)

        loader = QUiLoader()
        ui_file = QFile(str(_UI_FILE))
        ui_file.open(QFile.ReadOnly)
        central = loader.load(ui_file, self)
        ui_file.close()

        self.thumbnail_label = central.findChild(QLabel, "label_thumbnail")
        self.thumbnail_label.setText("")
        self.thumbnail_label.setMinimumHeight(_THUMBNAIL_FALLBACK_SIZE.height())
        self.repo_name_label = central.findChild(QLabel, "label_repo_name")
        self.repo_name_label.setText("No Repo Selected")
        self.repo_name_label.setWordWrap(True)

        self.tab_list = SectionTabList(
            central.findChild(QTableWidget, "tableWidget_tab"), section_registry=section_registry, parent=self
        )
        self.tab_list.navigation_changed.connect(self._on_navigation_changed)

        # widget_status/horizontalLayout_status (sync status label + progress
        # bar) was dropped from the .ui — no visible home for
        # SidebarFooterActionRegistry widgets anymore either, so their
        # factories still run (closeEvent still needs footer_action_widgets
        # to find a plugin's background_threads) but the resulting widget
        # is never parented into any layout. Currently a no-op either way —
        # nothing registers into this registry yet.
        for spec in self.sidebar_footer_action_registry.ordered():
            self.footer_action_widgets[spec.key] = spec.widget_factory()

        # listWidget_notification: any plugin can contribute its own row
        # here via api.register_notification(NotificationSpec(...)) — see
        # plugin_api/registries/notification_registry.py. Unlike
        # footer_action_widgets above, this list actually has a home in the
        # .ui, so each widget is really parented in as a row, not just kept
        # alive for closeEvent bookkeeping.
        self.notification_list = central.findChild(QListWidget, "listWidget_notification")
        for spec in self.notification_registry.ordered():
            widget = spec.widget_factory()
            self.notification_widgets[spec.key] = widget
            item = QListWidgetItem(self.notification_list)
            item.setSizeHint(widget.sizeHint())
            self.notification_list.addItem(item)
            self.notification_list.setItemWidget(item, widget)

        # label_username was dropped from the .ui — the signed-in username
        # is shown as pushButton_setting's own text now instead of a
        # separate label + icon button.
        self.setting_button = central.findChild(QPushButton, "pushButton_setting")
        self.setting_button.setText("")
        self.setting_button.setToolTip("Setting")
        self.setting_button.clicked.connect(lambda: self._on_settings_requested())

        # Every section (including Project Editor, folded into this stack
        # like any other section as of this refactor — it used to be
        # SectionSpec.persistent=True, always visible docked beside
        # view_stack in a QSplitter rather than switched to) is its own
        # full-width top-level page, switched to via the SectionTabList.
        # widget_tab_display/horizontalLayout_tab_display is an otherwise
        # empty placeholder in the .ui — view_stack itself is built here in
        # code, not authored as a widget, since it's populated from
        # SectionRegistry at runtime either way.
        self.view_stack = QStackedWidget()
        central.findChild(QHBoxLayout, "horizontalLayout_tab_display").addWidget(self.view_stack)
        self._section_view_index = {
            spec.key: self.view_stack.addWidget(self.pages[spec.key]) for spec in section_registry.ordered()
        }

        # Setting is a popup dialog (SettingsDialog), not a view_stack page
        # — see _on_settings_requested, which constructs one fresh on every
        # open. A repo node's "Repository Setting..." right-click opens this
        # same dialog (via UICommandService.open_settings_tab) rather than a
        # popup of its own.

        self.setCentralWidget(central)

        self.setMinimumHeight(MAIN_WINDOW_MIN_HEIGHT)
        # This runs synchronously inside __init__ — safe to resize()
        # unconditionally here because nothing ever calls
        # show()/showMaximized() before this point anymore (that's now
        # deferred to launcher.py's single QTimer.singleShot(0,
        # window.showMaximized), after app.exec() starts — see the
        # ukorehub-interface skill). The isMaximized() guard is kept anyway
        # as defense in depth, in case a future change adds an early show()
        # call back and needs this to stay safe against it.
        if not self.isMaximized() and self.height() < MAIN_WINDOW_MIN_HEIGHT:
            self.resize(self.width(), MAIN_WINDOW_MIN_HEIGHT)

    def _start_app(self) -> None:
        self.setting_button.setText(self.local_config_store.github_username or "")
        self._restore_active_repo()
        self._apply_to_current_page()
        self._setup_auto_git_identity()
        self._fire_app_started()

    def _setup_auto_git_identity(self) -> None:
        """ตั้งค่า git user.name และ user.email อัตโนมัติจาก GitHub Username ที่ล็อกอินอยู่"""
        github_username = self.local_config_store.github_username
        if not github_username:
            return

        email = f"{github_username.lower().replace(' ', '_')}@users.noreply.github.com"

        def apply_identity(context):
            if context.repo and context.repo_path.exists():
                try:
                    current_name = self.git_service._run_capture(["config", "user.name"], cwd=context.repo_path).strip()
                except Exception:
                    current_name = ""

                if not current_name:
                    self.git_service.set_user_identity(context.repo_path, github_username, email)
                    logging.getLogger("GitIdentity").info(
                        f"Auto-configured git identity for {context.repo.name}: {github_username}"
                    )

        # ผูกการทำงานเข้ากับ Hook ของระบบ
        self.hook_registry.subscribe_app_start(apply_identity)
        self.hook_registry.subscribe_repo_changed(apply_identity)

    # -- navigation (Explorer / Submit / About / Setting) --

    def _on_navigation_changed(self, key: str) -> None:
        index = self._section_view_index.get(key)
        if index is None:
            return
        self.view_stack.setCurrentIndex(index)
        self._apply_to_current_page()

    def _on_settings_requested(self, select_key: str | None = None) -> None:
        # Setting is its own icon button in Sidebar's footer, opened as a
        # popup dialog (reverted 2026-07-19 from an embedded view_stack
        # page back to a dialog — see SettingsDialog's own docstring) —
        # whatever section is showing behind it stays exactly as it was,
        # so unlike the old view_stack-page version there's no sidebar row
        # to deselect here. select_key lets a section's own "Open Setting"
        # button (via UICommandService.open_settings_tab) land directly on one
        # tab instead of whatever opens by default — see
        # plugin_api/registries/section_registry.py's UICommandService.
        dialog = SettingsDialog(self, settings_tab_registry=self.settings_tab_registry)
        common_settings_page = dialog.view.get_tab_widget(builtin_settings_tabs.COMMON)
        if common_settings_page is not None:
            common_settings_page.logout_requested.connect(self._on_logout_requested)
            # Logging out closes the whole app (see _on_logout_requested) —
            # close the dialog itself too rather than leaving it floating
            # over nothing.
            common_settings_page.logout_requested.connect(dialog.accept)
            common_settings_page.restart_requested.connect(self._on_restart_requested)
        if select_key is not None:
            dialog.select_tab(select_key)
        dialog.exec()

    def _set_status_message(self, message: str) -> None:
        # No-op — the sidebar's status label/progress bar were dropped from
        # the .ui. Kept as a real method (not removed) since
        # UICommandService.set_status_message is a required field plugins
        # call unconditionally (see plugins/core/submit/plugin.py's sync
        # start/finish/fail hooks).
        del message

    def _navigate_and_focus(self, key: str, path: Path) -> None:
        # A page (e.g. Submit's "Inspect in Explorer") asking to jump to
        # another section and focus a specific file there — switches the
        # sidebar row + view stack to `key`, then calls that page's optional
        # browse_to_path(path) protocol method if it implements one (see
        # plugin_api/registries/section_registry.py's UICommandService).
        self.tab_list.select(key)
        self._on_navigation_changed(key)
        page = self.pages.get(key)
        if isinstance(page, PathFocusablePage):
            page.browse_to_path(path)

    def _refresh_section(self, key: str) -> None:
        # Unlike _navigate_and_focus, this never touches the sidebar/
        # view_stack — a section (e.g. Submit after a sync) telling another
        # section (Explorer) its on-disk state changed shouldn't yank the
        # user's current tab. A no-op if the key doesn't resolve to a page,
        # or the page doesn't implement RefreshablePage (see
        # interface/page_protocols.py).
        page = self.pages.get(key)
        if isinstance(page, RefreshablePage):
            page.refresh_content()

    def _apply_plugin_visibility(self) -> None:
        """Hides the sidebar row of any plugins/ section the active repo
        doesn't currently want shown. A section with no entry in
        _section_key_to_plugin_id (e.g. the built-in "About" section) is
        never gated, so at least one row is always visible. Two different
        gating rules apply depending on where the section's plugin was
        discovered from (core.extensibility.loader.plugin_source):
        - plugins/core/ (self._core_plugin_ids) — always visible, no matter
          what (2026-08-04: no more per-repo opt-out here at all — anything
          repo-specific belongs under cache/plugins/ instead, so
          plugins/core/ is meant to be universal app-level functionality,
          e.g. Project Editor, where switching the active repo has no other
          entry point).
        - cache/plugins/ (self._opt_in_plugin_ids, plugin_source() "repo") —
          opt-in: hidden unless the plugin id is in Repo.required_plugin_ids.
          Each entry is its own separate git clone and never on by default.
          Same "off until required" shape as a Program requirement."""
        required_ids = self._active_repo.required_plugin_ids if self._active_repo is not None else []
        visible_keys = set()
        for key in self._section_view_index:
            plugin_id = self._section_key_to_plugin_id.get(key)
            if plugin_id is None or plugin_id in self._core_plugin_ids:
                visible_keys.add(key)
            elif plugin_id in self._opt_in_plugin_ids:
                if plugin_id in required_ids:
                    visible_keys.add(key)
        self.tab_list.set_visible_keys(visible_keys)

        current_key = next(
            (key for key, index in self._section_view_index.items() if index == self.view_stack.currentIndex()),
            None,
        )
        if current_key is not None and current_key not in visible_keys:
            # Insertion-order (registry order) fallback, same
            # determinism as _rebuild_dynamic_tabs' own fallback.
            fallback_key = next(key for key in self._section_view_index if key in visible_keys)
            self.tab_list.select(fallback_key)
            self._on_navigation_changed(fallback_key)

    # -- active repo -----------------------------------------------------

    def _set_active_repo_labels(self, repo_name: str | None, project_name: str | None = None) -> None:
        # Repo name only (project_name kept as a param for call-site
        # compatibility, but no longer shown) — the sidebar used to show
        # "Project / Repo" via ActiveRepoWidget, but that's redundant now
        # that Project is fixed for the whole run anyway.
        del project_name
        self.repo_name_label.setText(repo_name or "No Repo Selected")

    def _set_thumbnail(self, path: Path | None) -> None:
        pixmap = QPixmap(str(path)) if path and Path(path).exists() else None
        if pixmap is not None and pixmap.isNull():
            pixmap = None
        self._thumbnail_source_pixmap = pixmap
        self._apply_thumbnail_crop()

    def _apply_thumbnail_crop(self) -> None:
        # Fill-crop (never letterboxed), matching the old
        # ActiveRepoWidget/_ThumbnailBanner behavior. Re-run from
        # resizeEvent, not just from _set_thumbnail — label_thumbnail has
        # no real size yet the first time a repo is restored (that runs
        # before the window is ever shown/maximized), so cropping once
        # against a guessed fallback size left the image only filling part
        # of the label once the real (larger) layout size kicked in.
        if self._thumbnail_source_pixmap is None:
            self.thumbnail_label.clear()
            return
        label_size = self.thumbnail_label.size()
        if label_size.width() <= 0 or label_size.height() <= 0:
            return
        scaled = self._thumbnail_source_pixmap.scaled(label_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        x = max(0, (scaled.width() - label_size.width()) // 2)
        y = max(0, (scaled.height() - label_size.height()) // 2)
        self.thumbnail_label.setPixmap(scaled.copy(x, y, label_size.width(), label_size.height()))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Guarded with getattr, not a plain None check — Qt can deliver a
        # resizeEvent during super().__init__() itself, before
        # thumbnail_label even exists as an attribute yet.
        if getattr(self, "thumbnail_label", None) is not None:
            self._apply_thumbnail_crop()

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
        self._set_active_repo_labels(repo.name, project.name)
        self._set_thumbnail(self.store.resolve_thumbnail_path(repo))
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
        self._set_active_repo_labels(self._active_repo.name, self._active_project.name)
        self._set_thumbnail(self.store.resolve_thumbnail_path(self._active_repo))
        self._apply_plugin_visibility()
        self._apply_to_current_page()
        self._fire_repo_selected()

    def _fire_repo_selected(self) -> None:
        if not self.local_config_store.workspace_root:
            return
        repo_path = Path(self.local_config_store.workspace_root) / self._active_repo.local_path
        self.hook_registry.fire_repo_changed(
            AppLifecycleContext(project=self._active_project, repo=self._active_repo, repo_path=repo_path)
        )

    def _fire_app_started(self) -> None:
        workspace_root = self.local_config_store.workspace_root
        repo_path = Path(workspace_root) if workspace_root else Path.cwd()
        self.hook_registry.fire_app_start(
            AppLifecycleContext(project=self._active_project, repo=self._active_repo, repo_path=repo_path)
        )

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
        self.setting_button.setText("")
        self._relaunch_to_login()

    @staticmethod
    def _relaunch_to_login() -> None:
        # relaunch_ukorehub_exe (core/relaunch.py) owns the _PYI_-env-var
        # stripping needed here (see the ukorehub-interface skill) — shared
        # with launcher.py's own mandatory login gate, see that module's
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
        # Restart app via Launcher Only to ensure auto-update is working.
        if not relaunch_ukorehub_exe(_REPO_ROOT):
            # สำรองไว้สำหรับ Developer ที่รัน python launcher.py ตรงๆ ในโฟลเดอร์ app
            subprocess.Popen([sys.executable, *sys.argv], cwd=str(_REPO_ROOT))
        
        QApplication.quit()

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
        if self.footer_action_widgets:
            for spec in self.sidebar_footer_action_registry.ordered():
                if spec.background_threads is not None:
                    workers.extend(spec.background_threads(self.footer_action_widgets[spec.key]))
        if self.notification_widgets:
            for spec in self.notification_registry.ordered():
                if spec.background_threads is not None:
                    workers.extend(spec.background_threads(self.notification_widgets[spec.key]))
        if self.pages:
            for spec in self.section_registry.ordered():
                if spec.background_threads is not None:
                    workers.extend(spec.background_threads(self.pages[spec.key]))
        for thread in workers:
            if thread is not None and thread.isRunning():
                thread.terminate()
                thread.wait(3000)
        super().closeEvent(event)
