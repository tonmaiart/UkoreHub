from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.vcs.cloud_sync import R2JsonSync
from core_api import (
    AppLifecycleHandler,
    ConflictError,
    DiscoveredPlugin,
    FileOpenerRegistry,
    FileOpenerSpec,
    GitService,
    LocalConfigStore,
    MetadataStore,
    NotFoundError,
    PluginConfigStore,
    ProjectPluginConfigStore,
    Repo,
    SystemConfigStore,
    UkoreCore,
)
from plugin_api.registries.notification_registry import NotificationSpec
from plugin_api.registries.program_launch_registry import ProgramLaunchRegistry, ProgramLaunchSpec
from plugin_api.registries.section_registry import SectionSpec
from plugin_api.registries.settings_tab_registry import SettingsTabRegistry, SettingsTabSpec
from plugin_api.registries.sidebar_footer_action_registry import SidebarFooterActionSpec
from plugin_api.registries.ui_registry_manager import UIRegistryManager

PLUGIN_API_VERSION = 1

_cloud_sync_logger = logging.getLogger("CloudSync")


@dataclass(frozen=True)
class RepoContextDTO:
    """Read-only snapshot of "which project/repo is active right now" —
    the pure-read subset of what a plugin would otherwise reach
    api.metadata/api.local_config directly for. Built fresh on every
    api.repo_context access (same freshness contract as reading those
    stores directly — do not cache a returned DTO across a repo switch).

    This does not replace api.metadata/api.git for a plugin that needs to
    write to the registry or run git operations (clone/pull/push) — those
    still go through the real services. See PluginAPI.repo_context's own
    docstring for why a strictly read-only DTO can't cover that case."""

    project_id: str
    project_name: str
    repo_id: str
    repo_name: str
    repo_path: Path | None
    workspace_root: Path | None
    required_plugin_ids: tuple[str, ...]


class PluginAPI:
    """The object passed to every plugin's `register(api)` entry point.
    Composes the existing core/ services (unmodified — same objects the app
    itself uses) with the Qt-aware UI registries, since core/ stays Qt-free
    and section/settings-tab registration needs QWidget factories.

    `api.metadata`/`api.git`/`api.local_config` remain the sanctioned way
    to reach the real stores/git operations — every write and every
    background git operation (clone/pull/push/log) any plugin runs goes
    through one of these three. `api.repo_context` is a narrower,
    read-only addition for the common case of "which project/repo is
    active and where does it live on disk" — it doesn't replace the three
    above, since a read-only DTO architecturally can't cover writes or git
    operations (see that property's own docstring).

    Phase 1+2 exposes services as-is; hardening (e.g. excluding TokenStore,
    restricting writes) is a documented follow-up once untrusted third-party
    plugins are a real possibility — every plugin loaded today is studio- or
    self-authored."""

    def __init__(
        self,
        *,
        core: UkoreCore,
        registries: UIRegistryManager,
        plugins_data_dir: Path,
        plugins_local_dir: Path,
        cache_dir: Path,
        app_root: Path,
        cloud_sync: R2JsonSync | None = None,
        plugin_catalog: list[DiscoveredPlugin] = (),
    ):
        self._core = core
        self._section_registry = registries.sections
        self._settings_tab_registry = registries.settings_tabs
        self._file_opener_registry = registries.file_openers
        self._program_launch_registry = registries.program_launchers
        self._sidebar_footer_action_registry = registries.sidebar_footer_actions
        self._notification_registry = registries.notifications
        self._plugins_data_dir = Path(plugins_data_dir)
        self._plugins_local_dir = Path(plugins_local_dir)
        self._cache_dir = Path(cache_dir)
        self._app_root = Path(app_root)
        self._cloud_sync = cloud_sync
        self._plugin_catalog = list(plugin_catalog)

    @property
    def metadata(self) -> MetadataStore:
        return self._core.metadata

    @property
    def local_config(self) -> LocalConfigStore:
        return self._core.local_config

    @property
    def plugin_catalog(self) -> list[DiscoveredPlugin]:
        """Every plugin discover_plugins() loaded this launch (Core,
        Internal, and External/cache-plugins alike), the same list
        launcher.py threads into register_builtin_settings_tabs/the
        "Plugins" Developer tab. Read-only snapshot — for a plugin that
        needs to resolve another plugin's id to its manifest (name,
        requires, ...), e.g. plugins/core/project_editor/
        project_database_page.py showing a catalog entry's own requires."""
        return list(self._plugin_catalog)

    @property
    def system_config_store(self) -> SystemConfigStore:
        """Shared, cloud-synced studio config — the same object launcher.py
        threads into register_builtin_settings_tabs. For a plugin that
        needs direct read/write access to fields like r2_bucket_name or
        github_client_id."""
        return self._core.system_config

    @property
    def cache_dir(self) -> Path:
        """UkoreHub's own per-machine cache/ directory (gitignored) — for a
        plugin building its own per-machine state alongside
        cache/local_config.json. Same purpose as app_root, one directory
        over."""
        return self._cache_dir

    @property
    def cloud_sync(self) -> R2JsonSync | None:
        """Read-only access to the already-built cloud-sync engine — the
        same object plugin_config_store() already uses privately. None if
        cloud sync isn't configured/reachable for this run (see
        launcher.py's _build_cloud_sync — e.g. the shared UKOREHUB_R2_*
        env vars aren't set, or the bucket/network is unreachable).
        Decided once at startup."""
        return self._cloud_sync

    @property
    def git(self) -> GitService:
        return self._core.git

    @property
    def repo_context(self) -> RepoContextDTO | None:
        """Read-only snapshot of the active project/repo — project/repo
        id/name, the repo's resolved on-disk path, workspace_root,
        and required_plugin_ids. None when no repo is
        active yet (e.g. very first launch, before any repo has ever been
        selected).

        Deliberately does not replace api.metadata/api.git for anything
        beyond this read-only identity/path info: a plugin that writes to
        the registry (add_repo, set_repo_thumbnail, set_repo_plugin_data,
        ...) or runs a git operation (clone/pull/push/log, typically on a
        background QThread) still needs the real store/service, which a
        frozen snapshot dataclass architecturally cannot provide — see
        PluginAPI's own docstring."""
        local_config = self._core.local_config
        project_id = local_config.active_project_id
        repo_id = local_config.active_repo_id
        if project_id is None or repo_id is None:
            return None
        try:
            project = self._core.metadata.get_project(project_id)
            repo = self._core.metadata.get_repo(project_id, repo_id)
        except NotFoundError:
            return None
        workspace_root = Path(local_config.workspace_root) if local_config.workspace_root else None
        return RepoContextDTO(
            project_id=project.id,
            project_name=project.name,
            repo_id=repo.id,
            repo_name=repo.name,
            repo_path=(workspace_root / repo.local_path) if workspace_root is not None else None,
            workspace_root=workspace_root,
            required_plugin_ids=tuple(repo.required_plugin_ids),
        )

    @property
    def debug_log_handler(self):
        """The shared interface_api.QtLogHandler instance
        plugins/core/DebugConsole/'s viewer page reads/subscribes to — or
        None if no QApplication/launcher.py wiring exists (e.g. a bare test
        construction). Not meant for general plugin use: just call
        `logging.getLogger("YourPlugin").info(...)` directly instead, no api
        needed at all — this property exists solely for DebugConsole
        itself."""
        return self._core.debug_log_handler

    @property
    def file_opener_registry(self) -> FileOpenerRegistry:
        """Read access to the same registry register_file_opener() writes
        into — for a page (e.g. Explorer's RepoBrowserWidget) that needs to
        call find_opener() itself rather than contribute an opener."""
        return self._file_opener_registry

    @property
    def program_launch_registry(self) -> ProgramLaunchRegistry:
        """Read access to the same registry register_program_launcher()
        writes into — for plugins/core/software_linker/'s Program Launcher
        tab to look up a plugin-contributed launch behavior (e.g.
        maya_launcher's setProject/env-merge wiring) for a given Program,
        rather than always subprocess.Popen-ing the raw linked exe itself."""
        return self._program_launch_registry

    @property
    def settings_tab_registry(self) -> SettingsTabRegistry:
        """Read access to the same registry register_settings_tab() writes
        into — for a page (plugins/core/project_editor/'s right panel)
        that needs to enumerate every CATEGORY_REPO tab generically and
        render it itself, rather than contribute a tab of its own."""
        return self._settings_tab_registry

    @property
    def app_root(self) -> Path:
        """UkoreHub's own repo root — for plugins that need to reference
        other paths inside the UkoreHub installation itself (e.g. the
        vendored plugins/MayaToolkit/ tree), without guessing their own
        nesting depth from __file__."""
        return self._app_root

    def register_section(self, spec: SectionSpec) -> None:
        self._section_registry.register(spec)

    def register_settings_tab(self, spec: SettingsTabSpec) -> None:
        self._settings_tab_registry.register(spec)

    def register_file_opener(
        self,
        plugin_id: str,
        extensions: list[str],
        opener: Callable[[Path, Repo], bool],
    ) -> None:
        self._file_opener_registry.register(
            FileOpenerSpec(
                plugin_id=plugin_id,
                extensions=frozenset(e.lower() for e in extensions),
                opener=opener,
            )
        )

    def register_program_launcher(self, spec: ProgramLaunchSpec) -> None:
        self._program_launch_registry.register(spec)

    def register_sidebar_footer_action(self, spec: SidebarFooterActionSpec) -> None:
        self._sidebar_footer_action_registry.register(spec)

    def register_notification(self, spec: NotificationSpec) -> None:
        """Adds a plugin's own widget as a row in Sidebar's
        listWidget_notification — see NotificationSpec
        (plugin_api/registries/notification_registry.py)."""
        self._notification_registry.register(spec)

    def on_app_start(self, handler: AppLifecycleHandler) -> None:
        """Runs once, right after the app finishes launching (whichever
        repo is already active by then, if any)."""
        self._core.hooks.subscribe_app_start(handler)

    def on_repo_changed(self, handler: AppLifecycleHandler) -> None:
        """Runs every time the user switches the active repo."""
        self._core.hooks.subscribe_repo_changed(handler)

    def on_app_close(self, handler: AppLifecycleHandler) -> None:
        """Runs once, as the main window is closing."""
        self._core.hooks.subscribe_app_close(handler)

    def plugin_config_store(self, plugin_id: str, *, shared: bool = False) -> PluginConfigStore:
        # shared=True -> data/plugins/core/ (synced via Cloudflare R2,
        # core/vcs/cloud_sync.py — same for everyone, no longer git-tracked).
        # shared=False -> cache/plugin_local_config/ (gitignored, per-machine
        # — lives under cache/ rather than data/ so it's excluded the same
        # way UkoreHub.exe/developer/commit-main.ps1 already excludes cache/
        # when publishing a release).
        if not shared:
            return PluginConfigStore(self._plugins_local_dir / f"{plugin_id}.json")
        json_path = self._plugins_data_dir / "core" / f"{plugin_id}.json"
        blob_name = f"plugins/core/{plugin_id}.json"
        if self._cloud_sync is not None:
            try:
                self._cloud_sync.pull(blob_name, json_path)
                _cloud_sync_logger.info(f"pulled '{blob_name}'")
            except Exception as exc:
                # Same "never block on a cloud problem" rule as launcher.py's
                # startup pull — a timeout/auth failure here shouldn't stop
                # plugin registration, which runs synchronously at startup.
                print(f"UkoreHub: cloud pull of '{blob_name}' failed ({exc}) — using local copy.")
                _cloud_sync_logger.warning(f"pull of '{blob_name}' failed ({exc}) — using local copy")

        def _push_plugin_blob() -> None:
            if self._cloud_sync is None:
                return
            try:
                self._cloud_sync.push(blob_name, json_path)
                _cloud_sync_logger.info(f"pushed '{blob_name}'")
            except ConflictError as exc:
                _cloud_sync_logger.warning(f"push of '{blob_name}' conflicted ({exc}) — reloaded latest")
                raise
            except Exception as exc:
                print(f"UkoreHub: cloud push of '{blob_name}' failed ({exc}) — local copy saved, not yet synced.")
                _cloud_sync_logger.warning(f"push of '{blob_name}' failed ({exc}) — local copy saved, not yet synced")

        return PluginConfigStore(json_path, on_save=_push_plugin_blob)

    def project_plugin_config_store(self, plugin_id: str) -> ProjectPluginConfigStore | None:
        """Same get/set contract as plugin_config_store(shared=True), but
        scoped to the currently active Project (core/models.py's
        Project.plugin_data) instead of one studio-wide blob — for data
        that's inherently session/project-scoped rather than studio-wide
        (e.g. maya_launcher's MAYA_ENV_BRIDGE contributions). Returns None
        when no project is active yet (e.g. very first launch, before any
        project has ever been selected) — callers must handle this rather
        than assume a store is always available, same "never crash on a
        missing-context problem at startup" convention as the cloud-pull
        failure handling above."""
        project_id = self._core.local_config.active_project_id
        if project_id is None:
            return None
        return ProjectPluginConfigStore(self._core.metadata, project_id, plugin_id)
