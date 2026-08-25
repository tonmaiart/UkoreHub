"""plugin_api: the only import surface app/plugins/ code may use.

Facade over core/ (Qt-free stores/git/exceptions/models) plus the Qt-aware
UI registries (SectionRegistry, SettingsTabRegistry, ...) that used to live
in interface/ — moved here because PluginAPI already composed them, and a
plugin needs their spec/dataclass types (SectionSpec, SettingsTabSpec, ...)
to call api.register_section()/register_settings_tab() at all. interface/
now imports these registries from here too, rather than the other way
around.

This module re-exports every core/ symbol app/plugins/core/*'s files
currently need (models, exceptions, service types for constructor type
hints, plugin-loader dataclasses, ...) — sourced from `core_api` (the only
thing allowed to import `core.*` directly, see `app/core_api/__init__.py`)
rather than `core.*` itself — so a plugin file never has to write `from
core.xxx import yyy`: `from plugin_api import yyy` instead. Add a new
re-export here (not a direct `core.*`/`core_api.*` import in a plugin
file) whenever a plugin needs a new core/ type; if `core_api` doesn't
re-export it yet either, add it there first.

Same doctrine applies to UI pieces a plugin page needs (shared widgets,
theme helpers, the `LOCAL_REPOSITORY` settings-tab key) — sourced from
`interface_api` (the only thing besides `interface/` itself allowed to
import `interface.*` directly, see `app/interface_api/__init__.py`)
rather than `interface.*` itself. Add a new re-export here whenever a
plugin needs another `interface_api`-exposed symbol; if `interface_api`
doesn't re-export it yet either, add it there first.

Deliberately does not re-export core.vcs.cloud_sync.R2JsonSync (nor does
core_api) — that stays restricted to launcher.py and
plugin_api/plugin_api.py's own scoped `core.vcs.cloud_sync` import, so
boto3 never enters the frozen launcher exe's import graph (see
developer/app/docs/core-api.md's "What's deliberately not re-exported"
section). Use api.cloud_sync (the already-built instance) instead of
importing R2JsonSync directly.
"""
from __future__ import annotations

from core_api import (
    AppLifecycleContext,
    AppLifecycleHandler,
    ConflictError,
    DiscoveredPlugin,
    FileChange,
    FileOpenerRegistry,
    FileOpenerSpec,
    GitHubAuthError,
    GitOperationError,
    GitService,
    LocalConfigStore,
    MetadataStore,
    NotFoundError,
    PluginConfigStore,
    PluginManifest,
    Program,
    Project,
    ProjectPluginConfigStore,
    Repo,
    RepoStatus,
    SystemConfigStore,
    UkoreHubError,
    ValidationError,
    check_repo_access,
    extract_git_repo_name,
    fetch_avatar_bytes,
    open_in_file_explorer,
    open_with_default_app,
    plugin_source,
    relaunch_ukorehub_exe,
)

from plugin_api.plugin_api import PLUGIN_API_VERSION, PluginAPI, RepoContextDTO
from plugin_api.registries.notification_registry import NotificationRegistry, NotificationSpec
from plugin_api.registries.program_launch_registry import ProgramLaunchRegistry, ProgramLaunchSpec
from plugin_api.registries.registry_base import KeyedOrderedRegistry
from plugin_api.registries.section_registry import SectionRegistry, SectionSpec, UICommandService
from plugin_api.registries.settings_tab_registry import (
    CATEGORY_DEVELOPER,
    CATEGORY_GENERAL,
    CATEGORY_LABELS,
    CATEGORY_PROJECT,
    CATEGORY_REPO,
    SettingsTabRegistry,
    SettingsTabSpec,
)
from plugin_api.registries.sidebar_footer_action_registry import (
    SidebarFooterActionRegistry,
    SidebarFooterActionSpec,
)
from plugin_api.registries.ui_registry_manager import UIRegistryManager

# interface_api transitively imports interface.builtin_settings_tabs, which
# imports CATEGORY_*/SettingsTabRegistry/SettingsTabSpec back from this very
# module — must come after the registries imports above so those names are
# already bound here when that happens (see interface_api/__init__.py's own
# load-bearing-order note).
from interface_api import (
    CommitCard,
    CommitFilesDialog,
    CommitHistoryEntry,
    DEFAULT_THEME_NAME,
    LOCAL_REPOSITORY,
    QtLogHandler,
    RequirementsTreeWidget,
    confirm_action,
    fetch_entries_via_github,
    format_commit_date,
    format_relative_time,
    get_theme,
    pick_image_file,
    save_image_asset,
    set_bold,
    set_secondary_text,
    show_exclusive,
    wrap_scrollable,
)

__all__ = [
    "AppLifecycleContext",
    "AppLifecycleHandler",
    "CATEGORY_DEVELOPER",
    "CATEGORY_GENERAL",
    "CATEGORY_LABELS",
    "CATEGORY_PROJECT",
    "CATEGORY_REPO",
    "CommitCard",
    "CommitFilesDialog",
    "CommitHistoryEntry",
    "ConflictError",
    "DEFAULT_THEME_NAME",
    "DiscoveredPlugin",
    "FileChange",
    "FileOpenerRegistry",
    "FileOpenerSpec",
    "GitHubAuthError",
    "GitOperationError",
    "GitService",
    "KeyedOrderedRegistry",
    "LOCAL_REPOSITORY",
    "LocalConfigStore",
    "MetadataStore",
    "NotFoundError",
    "NotificationRegistry",
    "NotificationSpec",
    "PLUGIN_API_VERSION",
    "PluginAPI",
    "PluginConfigStore",
    "PluginManifest",
    "Program",
    "ProgramLaunchRegistry",
    "ProgramLaunchSpec",
    "Project",
    "ProjectPluginConfigStore",
    "QtLogHandler",
    "Repo",
    "RepoContextDTO",
    "RepoStatus",
    "RequirementsTreeWidget",
    "SectionRegistry",
    "SectionSpec",
    "SettingsTabRegistry",
    "SettingsTabSpec",
    "SidebarFooterActionRegistry",
    "SidebarFooterActionSpec",
    "SystemConfigStore",
    "UICommandService",
    "UIRegistryManager",
    "UkoreHubError",
    "ValidationError",
    "check_repo_access",
    "confirm_action",
    "extract_git_repo_name",
    "fetch_avatar_bytes",
    "fetch_entries_via_github",
    "format_commit_date",
    "format_relative_time",
    "get_theme",
    "open_in_file_explorer",
    "open_with_default_app",
    "pick_image_file",
    "plugin_source",
    "relaunch_ukorehub_exe",
    "save_image_asset",
    "set_bold",
    "set_secondary_text",
    "show_exclusive",
    "wrap_scrollable",
]
