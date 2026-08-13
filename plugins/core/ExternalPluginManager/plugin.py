from __future__ import annotations

from plugin_api import CATEGORY_PROJECT, AppLifecycleContext, SettingsTabSpec
from plugins.core.ExternalPluginManager.catalog_store import ExternalPluginCatalog
from plugins.core.ExternalPluginManager.external_plugins_page import ExternalPluginsPage
from plugins.core.ExternalPluginManager.last_check_store import LastCheckedStore
from plugins.core.ExternalPluginManager.sync_engine import PERSISTENT_STATUSES
from plugins.core.ExternalPluginManager.sync_status_store import ExternalPluginSyncStatusStore
from plugins.core.ExternalPluginManager.sync_worker import ExternalPluginSyncWorker

PLUGIN_ID = "external_plugins"


class _SyncController:
    """Owns the auto-sync engine for the whole app session. Built once in
    register(api) below; stays alive purely because api.on_app_start/
    on_repo_changed hold a reference to one of its bound methods — see
    AppLifecycleHooks (core/events/hooks.py), whose handler lists live as
    long as the app does. No module-level global needed for that reason.

    Runs at most one ExternalPluginSyncWorker at a time (plan: "Overlapping
    syncs must not run concurrent git commands on the same folder") — a
    trigger that arrives while one is still running replaces
    self._pending_context (keeping only the latest) instead of starting a
    second worker; _on_finished starts exactly one more run for it once the
    in-flight one completes."""

    def __init__(self, api) -> None:
        self._api = api
        self._git_service = api.git
        # api.cache_dir, not api.app_root — CACHE_DIR is launcher.py's own
        # (usually outside app/ entirely, e.g. ~/Documents/UkoreHub/cache
        # unless UKOREHUB_CACHE_DIR overrides it; see root CLAUDE.md's
        # "Program folder stays program-only") notion of where
        # cache/plugins/ really lives, matching exactly what launcher.py
        # itself passes discover_plugins() (cache_plugins_root there) — see
        # the ukorehub-interface skill's PluginAPI section.
        self._plugins_root = api.cache_dir / "plugins"
        # Scoped to the active Project (Project.plugin_data), not a
        # studio-wide shared=True blob anymore — see catalog_store.py's own
        # docstring. active_project_id is fixed for the whole app session
        # (launcher.py's Project Selector gate runs before plugin
        # registration, and switching projects mid-session means a full
        # restart back through that gate — see core/storage/config_store.py's
        # LocalConfigStore.set_active_project), so building this once here
        # and holding it for the session is safe, same as before.
        self.catalog = ExternalPluginCatalog(api.project_plugin_config_store(PLUGIN_ID))
        self.status_store = ExternalPluginSyncStatusStore(api.plugin_config_store(PLUGIN_ID, shared=False))
        # Separate top-level key from status_store's own "sync_status" (see
        # last_check_store.py's own docstring) — sharing one record would let
        # an unrelated auto-sync clear-on-success wipe out a manual Check for
        # Status result.
        self.last_check_store = LastCheckedStore(api.plugin_config_store(PLUGIN_ID, shared=False))
        self._worker: ExternalPluginSyncWorker | None = None
        self._pending_context: AppLifecycleContext | None = None

    def on_lifecycle_event(self, context: AppLifecycleContext) -> None:
        if context.repo is None:
            return
        if self._worker is not None and self._worker.isRunning():
            self._pending_context = context
            return
        self._start(context)

    def _start(self, context: AppLifecycleContext) -> None:
        worker = ExternalPluginSyncWorker(
            git_service=self._git_service,
            plugins_root=self._plugins_root,
            repo=context.repo,
            catalog=self.catalog,
            plugin_catalog=self._api.plugin_catalog,
        )
        worker.entry_synced.connect(self._on_entry_synced)
        worker.backfill_ready.connect(self._on_backfill_ready)
        worker.finished.connect(self._on_finished)
        self._worker = worker
        worker.start()

    def _on_entry_synced(self, entry_id: str, status: str, message: str) -> None:
        if status in PERSISTENT_STATUSES:
            self.status_store.set(entry_id, status, message)
        else:
            self.status_store.clear(entry_id)
        detail = f" — {message}" if message else ""
        self._api.debug_bus.log("ExternalPluginManager", f"{entry_id}: {status}{detail}")

    def _on_backfill_ready(self, entry_id: str, plugin_id: str) -> None:
        self.catalog.update_plugin_id(entry_id, plugin_id)

    def _on_finished(self) -> None:
        self._worker = None
        if self._pending_context is not None:
            context, self._pending_context = self._pending_context, None
            self._start(context)


def register(api) -> None:
    # A fresh page per Settings open (same page_factory convention as every
    # other Settings tab — see interface/settings/settings_view.py's
    # SettingsView docstring), but the sync controller itself is built once
    # for the whole app session so its background sync survives across
    # Settings dialog opens/closes.
    sync_controller = _SyncController(api)
    api.on_app_start(sync_controller.on_lifecycle_event)
    api.on_repo_changed(sync_controller.on_lifecycle_event)

    api.register_settings_tab(
        SettingsTabSpec(
            key=PLUGIN_ID,
            label="External Plugin Manager",
            # After Settings > Project's built-in "Project" (order=0) and
            # "Program Database" (order=20) tabs — see
            # interface/builtin_settings_tabs.py and
            # plugins/core/project_editor/plugin.py.
            order=30,
            page_factory=lambda: ExternalPluginsPage(
                git_service=api.git,
                plugins_root=api.cache_dir / "plugins",  # see _SyncController's own comment on this
                catalog=sync_controller.catalog,
                plugin_catalog=api.plugin_catalog,
                sync_status_store=sync_controller.status_store,
                last_check_store=sync_controller.last_check_store,
            ),
            category=CATEGORY_PROJECT,
        )
    )
