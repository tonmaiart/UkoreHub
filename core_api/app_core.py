"""UkoreCore: composition facade for core/'s stateful services.

Collects the objects launcher.py used to construct one at a time
(MetadataStore, SystemConfigStore, LocalConfigStore, AppLifecycleHooks,
GitService, SecureTokenStore x2, DebugLogBus) behind a
single object, so MainWindow/PluginAPI each take one `core` param instead
of wiring each service individually.

Deliberately never imports core.vcs.cloud_sync — the on_save/on_delete
hooks for the cloud-synced stores are still passed in as plain callables
from launcher.py, the same DI pattern MetadataStore/SystemConfigStore
already used before this facade existed. This is load-bearing, not a style
choice: see developer/app/docs/core-api.md's "What's deliberately not
re-exported" section — only launcher.py and plugin_api/plugin_api.py may
import core.vcs.cloud_sync, never core/storage/*.py (and by extension,
never this module), so boto3 never ends up in updater.py
(UkoreHubLauncher repo)'s frozen-exe import graph.

Cloud pull/push orchestration and the mandatory GitHub-login gate (Qt
dialogs) stay in launcher.py — they either need to run before this class
can be constructed (the bucket name has to come from somewhere before
SystemConfigStore exists) or are Qt-bound, which core/ never is. There is
no per-user cloud login anymore (a single shared R2 key, injected via
UKOREHUB_R2_* env vars, replaces the old per-artist Google OAuth token),
so unlike GitHub's SecureTokenStore below, no analogous token store exists
for cloud sync at all.

debug_bus is accepted as an optional constructor param rather than always
built internally, because launcher.py needs a debug bus *before* UkoreCore
can be constructed (the cloud-bootstrap pull sequence that determines
system_config's bucket name runs first, and already logs to it). When not
supplied (the common case, and every case in tests), a fresh instance is
built here instead — same optional-injection shape `on_save` already
uses.

Lives in app/core_api/ (not app/core/) since app/core/ is closed — nothing
outside app/core/ and app/core_api/ may import core.* directly (see
developer/app/check_import_boundaries.py). This module is core_api's own
facade-construction site, so it's the one place allowed to import core.*
submodules directly; everything else imports UkoreCore (and every other
core/ type it needs) from core_api instead — see core_api/__init__.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.auth.token_store import SecureTokenStore
from core.events.bus import InMemoryEventBus
from core.events.debug_log import DebugLogBus
from core.events.hooks import AppLifecycleHooks
from core.models import Project, Repo
from core.storage.config_store import LocalConfigStore, SystemConfigStore
from core.storage.metadata_store import MetadataStore
from core.vcs.git_service import GitService


class UkoreCore:
    def __init__(
        self,
        *,
        data_dir: Path,
        cache_dir: Path,
        assets_dir: Path,
        on_metadata_save: Callable[[str], None] | None = None,
        on_metadata_delete: Callable[[str], None] | None = None,
        on_system_config_save: Callable[[], None] | None = None,
        debug_bus: DebugLogBus | None = None,
    ):
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.metadata = MetadataStore(
            self.data_dir / "projects.json",
            assets_dir=assets_dir,
            on_save=on_metadata_save,
            on_delete=on_metadata_delete,
        )
        self.system_config = SystemConfigStore(
            self.data_dir / "system_config.json", on_save=on_system_config_save
        )
        self.local_config = LocalConfigStore(self.cache_dir / "local_config.json")
        self.hooks = AppLifecycleHooks()
        self.git = GitService()
        self.github_tokens = SecureTokenStore(
            "UkoreHub", "github_access_token", self.cache_dir / "github_token.json", token_label="GitHub"
        )
        self.debug_bus: InMemoryEventBus = debug_bus or DebugLogBus(max_entries=1000)

    def get_active_workspace(self) -> tuple[Project | None, Repo | None]:
        """The Project/Repo local_config currently points at, or (None, None)
        if nothing's active yet or the ids no longer resolve (e.g. the repo
        was deleted elsewhere)."""
        project_id = self.local_config.active_project_id
        repo_id = self.local_config.active_repo_id
        if not project_id or not repo_id:
            return None, None
        try:
            project = self.metadata.get_project(project_id)
            repo = self.metadata.get_repo(project_id, repo_id)
        except Exception:
            return None, None
        return project, repo

    def switch_active_repo(self, project_id: str, repo_id: str) -> None:
        self.local_config.set_active_repo(project_id, repo_id)

    def clear_github_session(self) -> None:
        """Clears the cached GitHub token and remembered username/login-at
        fields — the non-Qt half of logout. Does not relaunch UkoreHub.exe;
        that's the caller's job (interface/main_window.py's
        _relaunch_to_login), since core/ never touches Qt or spawns
        processes on its own."""
        self.github_tokens.clear_token()
        self.local_config.set_github_username(None)
        self.local_config.set_github_login_at(None)
        self.git.set_github_token(None)
