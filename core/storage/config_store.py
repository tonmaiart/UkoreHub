from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from core.storage.atomic_file import atomic_write

LOCAL_CONFIG_SCHEMA_VERSION = 1
SYSTEM_CONFIG_SCHEMA_VERSION = 1

# Duplicated from interface/theme.py's DEFAULT_THEME_NAME rather than imported:
# core/ never depends on interface/ (see core/README.md), and this store only
# needs the name as a persisted default, not the actual theme registry.
DEFAULT_THEME_NAME = "grey_dark"


class LocalConfigStore:
    """Per-machine settings — never shared, gitignored.

    Each artist's own workspace folder, theme preference, and "what am I
    currently working on" state live here, separate from the team-shared
    SystemConfigStore and the shared MetadataStore registry.
    """

    def __init__(self, json_path: Path):
        self.json_path = Path(json_path)
        self.workspace_root: str | None = None
        self.theme: str = DEFAULT_THEME_NAME
        self.active_project_id: str | None = None
        self.active_repo_id: str | None = None
        self.github_username: str | None = None
        self.github_login_at: str | None = None
        self.load()

    def load(self) -> None:
        if not self.json_path.exists():
            return
        data = json.loads(self.json_path.read_text(encoding="utf-8"))
        self.workspace_root = data.get("workspace_root")
        self.theme = data.get("theme", DEFAULT_THEME_NAME)
        self.active_project_id = data.get("active_project_id")
        self.active_repo_id = data.get("active_repo_id")
        self.github_username = data.get("github_username")
        self.github_login_at = data.get("github_login_at")

    def save(self) -> None:
        atomic_write(
            self.json_path,
            {
                "schema_version": LOCAL_CONFIG_SCHEMA_VERSION,
                "workspace_root": self.workspace_root,
                "theme": self.theme,
                "active_project_id": self.active_project_id,
                "active_repo_id": self.active_repo_id,
                "github_username": self.github_username,
                "github_login_at": self.github_login_at,
            },
        )

    def set_workspace_root(self, path: str) -> None:
        self.workspace_root = path
        self.save()

    def set_theme(self, name: str) -> None:
        self.theme = name
        self.save()

    def set_active_repo(self, project_id: str, repo_id: str) -> None:
        self.active_project_id = project_id
        self.active_repo_id = repo_id
        self.save()

    def set_active_project(self, project_id: str | None) -> None:
        """Fixes which Project this run is scoped to — called once by
        launcher.py's mandatory Project Selector gate before MainWindow/
        plugins are constructed, never mid-session (see
        plugins/core/project_editor's Settings > Project tab, which only
        offers "Switch Project" — a full app restart back through that same
        gate, interface/main_window.py's _request_switch_project). Clears
        active_repo_id too: a repo id left over from a previously active
        project would otherwise resolve against the wrong project's registry."""
        self.active_project_id = project_id
        self.active_repo_id = None
        self.save()

    def clear_active_repo(self) -> None:
        self.active_project_id = None
        self.active_repo_id = None
        self.save()

    def set_github_username(self, username: str | None) -> None:
        self.github_username = username
        self.save()

    def set_github_login_at(self, timestamp: str | None) -> None:
        self.github_login_at = timestamp
        self.save()


class SystemConfigStore:
    """Studio-wide settings shared to everyone via Cloudflare R2 (see
    core/vcs/cloud_sync.py), the same way the MetadataStore registry
    (data/projects.json) is shared. `on_save`, when provided by the caller,
    pushes the freshly-saved file up to the shared bucket.

    Only the bucket *name* lives here — it isn't secret. The R2 account
    id/access key/secret never do (see
    developer/launcher/launcher_build/r2_credentials.py); this store is
    itself one of the things synced through those credentials, so storing
    them here would be circular.
    """

    def __init__(self, json_path: Path, *, on_save: Callable[[], None] | None = None):
        self.json_path = Path(json_path)
        self.github_client_id: str | None = None
        self.r2_bucket_name: str | None = None
        self.on_save = on_save
        self.load()

    def load(self) -> None:
        if not self.json_path.exists():
            return
        data = json.loads(self.json_path.read_text(encoding="utf-8"))
        self.github_client_id = data.get("github_client_id")
        self.r2_bucket_name = data.get("r2_bucket_name")

    def save(self) -> None:
        atomic_write(
            self.json_path,
            {
                "schema_version": SYSTEM_CONFIG_SCHEMA_VERSION,
                "github_client_id": self.github_client_id,
                "r2_bucket_name": self.r2_bucket_name,
            },
        )
        if self.on_save:
            self.on_save()

    def set_github_client_id(self, client_id: str) -> None:
        self.github_client_id = client_id or None
        self.save()

    def set_r2_bucket_name(self, bucket_name: str) -> None:
        self.r2_bucket_name = bucket_name or None
        self.save()
