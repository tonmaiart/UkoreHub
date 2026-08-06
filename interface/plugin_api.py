from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.extensibility.config_store import PluginConfigStore
from core.extensibility.file_opener import FileOpenerRegistry, FileOpenerSpec
from core.extensibility.hooks import GitHookEvent, HookHandler, HookRegistry
from core.git_service import GitService
from core.models import Repo
from core.program_store import ProgramStore
from core.store import LocalConfigStore, MetadataStore
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
        program_store: ProgramStore,
        local_config_store: LocalConfigStore,
        git_service: GitService,
        hooks: HookRegistry,
        section_registry: SectionRegistry,
        settings_tab_registry: SettingsTabRegistry,
        file_opener_registry: FileOpenerRegistry,
        program_launch_registry: ProgramLaunchRegistry,
        sidebar_footer_action_registry: SidebarFooterActionRegistry,
        plugins_data_dir: Path,
        app_root: Path,
    ):
        self._store = store
        self._program_store = program_store
        self._local_config_store = local_config_store
        self._git_service = git_service
        self._hooks = hooks
        self._section_registry = section_registry
        self._settings_tab_registry = settings_tab_registry
        self._file_opener_registry = file_opener_registry
        self._program_launch_registry = program_launch_registry
        self._sidebar_footer_action_registry = sidebar_footer_action_registry
        self._plugins_data_dir = Path(plugins_data_dir)
        self._app_root = Path(app_root)

    @property
    def metadata(self) -> MetadataStore:
        return self._store

    @property
    def programs(self) -> ProgramStore:
        return self._program_store

    @property
    def local_config(self) -> LocalConfigStore:
        return self._local_config_store

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
        subdir = "core" if shared else "local"
        return PluginConfigStore(self._plugins_data_dir / subdir / f"{plugin_id}.json")
