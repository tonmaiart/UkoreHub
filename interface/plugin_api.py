from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.cloud_sync import GcsJsonSync
from core.exceptions import ConflictError
from core.extensibility import debug_log
from core.extensibility.config_store import PluginConfigStore, ProjectPluginConfigStore
from core.extensibility.file_opener import FileOpenerRegistry, FileOpenerSpec
from core.extensibility.hooks import GitHookEvent, HookHandler, HookRegistry
from core.git_service import GitService
from core.models import Repo
from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
from interface.program_launch_registry import ProgramLaunchRegistry, ProgramLaunchSpec
from interface.section_registry import SectionRegistry, SectionSpec
from interface.settings_tab_registry import SettingsTabRegistry, SettingsTabSpec
from interface.sidebar_footer_action_registry import SidebarFooterActionRegistry, SidebarFooterActionSpec

PLUGIN_API_VERSION = 1


class PluginAPI:
    """The object passed to every plugin's `register(api)` entry point.
    Composes the existing core/ services (unmodified — same objects the app
    itself uses) with the Qt-aware UI registries, since core/ stays Qt-free
    and section/settings-tab registration needs QWidget factories.

    Phase 1+2 exposes services as-is; hardening (e.g. excluding TokenStore,
    restricting writes) is a documented follow-up once untrusted third-party
    plugins are a real possibility — every plugin loaded today is studio- or
    self-authored."""

    def __init__(
        self,
        *,
        store: MetadataStore,
        local_config_store: LocalConfigStore,
        system_config_store: SystemConfigStore,
        git_service: GitService,
        hooks: HookRegistry,
        section_registry: SectionRegistry,
        settings_tab_registry: SettingsTabRegistry,
        file_opener_registry: FileOpenerRegistry,
        program_launch_registry: ProgramLaunchRegistry,
        sidebar_footer_action_registry: SidebarFooterActionRegistry,
        plugins_data_dir: Path,
        plugins_local_dir: Path,
        cache_dir: Path,
        app_root: Path,
        cloud_sync: GcsJsonSync | None = None,
    ):
        self._store = store
        self._local_config_store = local_config_store
        self._system_config_store = system_config_store
        self._git_service = git_service
        self._hooks = hooks
        self._section_registry = section_registry
        self._settings_tab_registry = settings_tab_registry
        self._file_opener_registry = file_opener_registry
        self._program_launch_registry = program_launch_registry
        self._sidebar_footer_action_registry = sidebar_footer_action_registry
        self._plugins_data_dir = Path(plugins_data_dir)
        self._plugins_local_dir = Path(plugins_local_dir)
        self._cache_dir = Path(cache_dir)
        self._app_root = Path(app_root)
        self._cloud_sync = cloud_sync

    @property
    def metadata(self) -> MetadataStore:
        return self._store

    @property
    def local_config(self) -> LocalConfigStore:
        return self._local_config_store

    @property
    def system_config_store(self) -> SystemConfigStore:
        """Shared, cloud-synced studio config — the same object launcher.py
        threads into register_builtin_settings_tabs. For a plugin (e.g.
        plugins/core/CloudConfig/) that needs direct read/write access to
        the gcs_*/google_oauth_* fields."""
        return self._system_config_store

    @property
    def cache_dir(self) -> Path:
        """UkoreHub's own per-machine cache/ directory (gitignored) — for a
        plugin building its own per-machine state alongside
        cache/local_config.json/cache/gcs_refresh_token.json, e.g.
        constructing core/google_auth.py's GoogleTokenStore(api.cache_dir /
        "gcs_refresh_token.json"). Same purpose as app_root, one directory
        over."""
        return self._cache_dir

    @property
    def cloud_sync(self) -> GcsJsonSync | None:
        """Read-only access to the already-built cloud-sync engine — the
        same object plugin_config_store() already uses privately. None if
        cloud sync isn't configured/logged-in for this run (see
        launcher.py's _build_cloud_sync). Decided once at startup —
        completing login mid-session won't flip this until UkoreHub
        restarts."""
        return self._cloud_sync

    @property
    def git(self) -> GitService:
        return self._git_service

    @property
    def file_opener_registry(self) -> FileOpenerRegistry:
        """Read access to the same registry register_file_opener() writes
        into — for a page (e.g. Explorer's RepoBrowserWidget) that needs to
        call find_opener() itself rather than contribute an opener."""
        return self._file_opener_registry

    @property
    def program_launch_registry(self) -> ProgramLaunchRegistry:
        """Read access to the same registry register_program_launcher()
        writes into — for plugins/core/program_launcher/'s card grid to
        look up a plugin-contributed launch behavior (e.g. maya_launcher's
        setProject/env-merge wiring) for a given Program, rather than
        always subprocess.Popen-ing the raw linked exe itself."""
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

    def register_git_hook(self, event: GitHookEvent, handler: HookHandler) -> None:
        self._hooks.subscribe(event, handler)

    def plugin_config_store(self, plugin_id: str, *, shared: bool = False) -> PluginConfigStore:
        # shared=True -> data/plugins/core/ (synced via Google Cloud Storage,
        # core/cloud_sync.py — same for everyone, no longer git-tracked).
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
                debug_log.log("CloudSync", f"pulled '{blob_name}'")
            except Exception as exc:
                # Same "never block on a cloud problem" rule as launcher.py's
                # startup pull — a timeout/auth failure here shouldn't stop
                # plugin registration, which runs synchronously at startup.
                print(f"UkoreHub: cloud pull of '{blob_name}' failed ({exc}) — using local copy.")
                debug_log.log("CloudSync", f"pull of '{blob_name}' failed ({exc}) — using local copy")

        def _push_plugin_blob() -> None:
            if self._cloud_sync is None:
                return
            try:
                self._cloud_sync.push(blob_name, json_path)
                debug_log.log("CloudSync", f"pushed '{blob_name}'")
            except ConflictError as exc:
                debug_log.log("CloudSync", f"push of '{blob_name}' conflicted ({exc}) — reloaded latest")
                raise
            except Exception as exc:
                print(f"UkoreHub: cloud push of '{blob_name}' failed ({exc}) — local copy saved, not yet synced.")
                debug_log.log("CloudSync", f"push of '{blob_name}' failed ({exc}) — local copy saved, not yet synced")

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
        project_id = self._local_config_store.active_project_id
        if project_id is None:
            return None
        return ProjectPluginConfigStore(self._store, project_id, plugin_id)
