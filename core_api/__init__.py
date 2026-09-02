"""core_api: the only import surface for app/core/'s internals.

app/core/ is closed — nothing outside app/core/ and app/core_api/ may
import core.* directly (see developer/app/check_import_boundaries.py).
`interface/`, `launcher.py`, and `plugin_api/`'s own facade files (which
still legitimately reach into core.* directly, same as this module does)
import types from here instead of `from core.xxx import yyy`.

Re-exports UkoreCore (core_api/app_core.py, the composition facade
launcher.py constructs once) plus every other core/ type interface/ and
launcher.py currently need — models, exceptions, service types (for
constructor type hints — the real shared instances always come from
`core.metadata`/`core.git`/`core.local_config` on a `UkoreCore` instance,
never construct these yourself), plugin-loader functions/dataclasses,
version constants, and a few narrowly-scoped helpers (relaunch,
migrate_legacy_programs, github_auth's avatar fetch, commits_api).

Deliberately does not re-export core.vcs.cloud_sync.R2JsonSync — that
stays restricted to launcher.py and plugin_api/plugin_api.py's own scoped
imports, so boto3 never enters the frozen launcher exe's import graph (see
developer/app/docs/core-api.md's "What's deliberately not re-exported"
section, and core_api/app_core.py's own docstring — UkoreCore itself
never imports it either).
"""
from __future__ import annotations

from core.auth.github_auth import fetch_avatar_bytes
from core.events.hooks import AppLifecycleContext, AppLifecycleHandler
from core.exceptions import (
    ConflictError,
    GitHubAuthError,
    GitOperationError,
    NotFoundError,
    UkoreHubError,
    ValidationError,
)
from core.extensibility.config_store import PluginConfigStore, ProjectPluginConfigStore
from core.extensibility.file_opener import FileOpenerRegistry, FileOpenerSpec
from core.extensibility.loader import (
    DiscoveredPlugin,
    PluginLoadFailure,
    PluginManifest,
    apply_plugins,
    discover_plugins,
    plugin_source,
)
from core.models import FileChange, Program, Project, Repo, RepoStatus
from core.os_utils import open_in_file_explorer, open_with_default_app
from core.relaunch import relaunch_ukorehub_exe
from core.storage.config_store import LocalConfigStore, SystemConfigStore
from core.storage.metadata_store import MetadataStore, migrate_legacy_programs, read_project_ids
from core.time_utils import format_relative_datetime, parse_iso_datetime
from core.vcs.commits_api import GitHubCommitsApiError, download_bytes, fetch_commits_for_path
from core.vcs.git_service import GitService
from core.vcs.paths import extract_git_repo_name
from core.vcs.repo_access import check_repo_access
from core.version import APP_NAME, APP_VERSION

from core_api.app_core import UkoreCore

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "AppLifecycleContext",
    "AppLifecycleHandler",
    "ConflictError",
    "DiscoveredPlugin",
    "FileChange",
    "FileOpenerRegistry",
    "FileOpenerSpec",
    "GitHubAuthError",
    "GitHubCommitsApiError",
    "GitOperationError",
    "GitService",
    "LocalConfigStore",
    "MetadataStore",
    "NotFoundError",
    "PluginConfigStore",
    "PluginLoadFailure",
    "PluginManifest",
    "Program",
    "Project",
    "ProjectPluginConfigStore",
    "Repo",
    "RepoStatus",
    "SystemConfigStore",
    "UkoreCore",
    "UkoreHubError",
    "ValidationError",
    "apply_plugins",
    "check_repo_access",
    "discover_plugins",
    "download_bytes",
    "extract_git_repo_name",
    "fetch_avatar_bytes",
    "fetch_commits_for_path",
    "format_relative_datetime",
    "migrate_legacy_programs",
    "open_in_file_explorer",
    "open_with_default_app",
    "parse_iso_datetime",
    "plugin_source",
    "read_project_ids",
    "relaunch_ukorehub_exe",
]
