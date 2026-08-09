"""UkoreHub entry point.

Bootstraps missing Python package dependencies before importing anything
that needs them, so the user never sees a ModuleNotFoundError.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REQUIRED_PACKAGES = [
    ("PySide6", "PySide6>=6.7,<7.0"),
    ("keyring", "keyring>=24.0"),
    ("google.cloud.storage", "google-cloud-storage>=2.16"),
    ("google_auth_oauthlib", "google-auth-oauthlib>=1.2"),
]

GIT_DOWNLOAD_URL = "https://github.com/git-for-windows/git/releases/download/v2.55.0.windows.3/Git-2.55.0.3-64-bit.exe"


def ensure_dependencies() -> None:
    for import_name, pip_spec in REQUIRED_PACKAGES:
        try:
            # find_spec on a dotted name (e.g. "google.cloud.storage") tries
            # to import the parent package first — if that parent isn't
            # installed at all yet, it raises ModuleNotFoundError instead of
            # just returning None, so that case needs its own catch too.
            found = importlib.util.find_spec(import_name) is not None
        except ModuleNotFoundError:
            found = False
        if found:
            continue
        print(f"UkoreHub: installing missing dependency '{pip_spec}'...")
        subprocess.run([sys.executable, "-m", "pip", "install", pip_spec], check=True)


# Presence checks only — no auto-install. UkoreHub.exe (updater.py in the
# UkoreHubLauncher repo) already checks/updates before this file is ever
# spawned; these only matter for the `python launcher.py` direct-invocation
# dev path, which bypasses that exe entirely.


def check_git_prerequisite() -> bool:
    return shutil.which("git") is not None


def check_git_lfs_prerequisite() -> bool:
    return shutil.which("git-lfs") is not None


def _build_cloud_sync(data_dir: Path, cache_dir: Path):
    """Best-effort: returns None (cloud sync disabled, the shared stores
    stay purely local — the pre-migration behavior) only if the bucket
    itself isn't configured yet. The bucket is public-read, so a machine
    with no cached Google refresh token (see core/google_auth.py's
    GoogleTokenStore — obtained via the "Studio" button, contributed by
    plugins/core/CloudConfig/'s plugin.py via the sidebar footer registry)
    still gets a real GcsJsonSync that can pull() anonymously; it just
    can't push() (see GcsJsonSync.can_push) until that artist logs in.
    Reads config fields off the raw local system_config.json rather than
    through SystemConfigStore, since that store is itself one of the
    things this function ends up syncing."""
    system_config_path = data_dir / "system_config.json"
    if not system_config_path.exists():
        return None
    config = json.loads(system_config_path.read_text(encoding="utf-8"))
    bucket_name = config.get("gcs_bucket_name")
    if not bucket_name:
        return None
    project_id = config.get("gcs_project_id")
    client_id = config.get("google_oauth_client_id")
    client_secret = config.get("google_oauth_client_secret")

    from core.google_auth import GoogleTokenStore

    refresh_token = GoogleTokenStore(cache_dir / "gcs_refresh_token.json").load_token()

    from core.cloud_sync import GcsJsonSync

    return GcsJsonSync(bucket_name, project_id, client_id, client_secret, refresh_token)


def main() -> None:
    ensure_dependencies()

    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication, QMessageBox

    app = QApplication(sys.argv)
    # icon.ico (UkoreHubLauncher repo) is only baked into UkoreHub.exe itself (via
    # PyInstaller's --icon) — that thin exe just spawns `pythonw
    # launcher.py` detached and exits (see exe_entry.py (UkoreHubLauncher repo)), so the
    # actual GUI process is plain python(w).exe and would otherwise show
    # Windows' generic Python icon in the taskbar/title bar unless the Qt
    # app sets its own window icon here.
    icon_path = REPO_ROOT / "developer" / "packaging" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    if not check_git_prerequisite():
        box = QMessageBox(
            QMessageBox.Icon.Critical,
            "Git Not Found",
            "UkoreHub requires 'git' to be installed and available on your PATH.\n"
            "Download and install it, then restart UkoreHub.",
        )
        download_button = box.addButton("Download Git", QMessageBox.ButtonRole.ActionRole)
        box.addButton(QMessageBox.StandardButton.Close)
        box.exec()
        if box.clickedButton() is download_button:
            webbrowser.open(GIT_DOWNLOAD_URL)
        sys.exit(1)

    if not check_git_lfs_prerequisite():
        QMessageBox.warning(
            None,
            "git-lfs Not Found",
            "'git-lfs' was not found on your PATH.\n"
            "Some repos may require it — you can continue, but LFS-tracked files "
            "may not sync correctly.",
        )

    from core.exceptions import ConflictError
    from core.extensibility import debug_log
    from core.extensibility.file_opener import FileOpenerRegistry
    from core.extensibility.hooks import HookRegistry
    from core.extensibility.loader import apply_plugins, discover_plugins, plugin_source
    from core.git_service import GitService
    from core.github.token_store import TokenStore
    from core.program_store import ProgramStore
    from core.relaunch import relaunch_ukorehub_exe
    from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
    from interface.builtin_settings_tabs import register_builtin_settings_tabs
    from interface.main_window import MainWindow
    from interface.plugin_api import PLUGIN_API_VERSION, PluginAPI
    from interface.program_launch_registry import ProgramLaunchRegistry
    from interface.section_registry import SectionRegistry
    from interface.settings_tab_registry import SettingsTabRegistry
    from interface.sidebar_footer_action_registry import SidebarFooterActionRegistry
    from interface.theme_apply import apply_theme

    data_dir = REPO_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    # cache/ is where every per-machine, gitignored file lives now (not
    # data/) — it's already excluded wholesale from UkoreHub.exe (git-
    # tracked) and from developer/commit-main.ps1's release publish, so
    # anything placed here can never accidentally ship in a release the way
    # a stray copy of data/ would. See cache/README.md.
    cache_dir = REPO_ROOT / "cache"
    cache_dir.mkdir(exist_ok=True)

    # projects.json, system_config.json, and programs.json are shared
    # studio-wide via Google Cloud Storage (core/cloud_sync.py), not git —
    # pull whatever's newest before constructing the stores that read them,
    # and wire on_save so every local edit pushes straight back up.
    cloud_sync = _build_cloud_sync(data_dir, cache_dir)
    if cloud_sync is None:
        print("UkoreHub: cloud sync not configured on this machine — shared data stays local-only.")
        debug_log.log("CloudSync", "not configured on this machine — shared data stays local-only")
    else:
        try:
            for blob_name in ("projects.json", "programs.json", "system_config.json"):
                cloud_sync.pull(blob_name, data_dir / blob_name)
                debug_log.log("CloudSync", f"pulled '{blob_name}'")
        except Exception as exc:
            # Revoked/expired Google login, no network, IAM not granted yet,
            # etc. — never block the app from opening over a cloud problem;
            # fall back to local-only for this run, same as "not configured
            # at all". The artist can re-run "Login with Google" in Setting
            # > Developer if this keeps happening.
            print(f"UkoreHub: cloud sync unavailable this run ({exc}) — shared data stays local-only.")
            debug_log.log("CloudSync", f"unavailable this run ({exc}) — shared data stays local-only")
            cloud_sync = None

    def _push_shared_blob(blob_name: str) -> None:
        if cloud_sync is None:
            return
        try:
            cloud_sync.push(blob_name, data_dir / blob_name)
            debug_log.log("CloudSync", f"pushed '{blob_name}'")
        except ConflictError as exc:
            # Meaningful to the caller (a real conflicting edit elsewhere) —
            # let it propagate so the UI can tell the artist and reload.
            debug_log.log("CloudSync", f"push of '{blob_name}' conflicted ({exc}) — reloaded latest")
            raise
        except Exception as exc:
            # Timeout, no network, revoked login, etc. — the local save
            # already succeeded (on_save fires after _atomic_write), so
            # don't fail the whole edit over a transient cloud problem;
            # just warn. The next successful save catches this file back up.
            print(f"UkoreHub: cloud push of '{blob_name}' failed ({exc}) — local copy saved, not yet synced.")
            debug_log.log("CloudSync", f"push of '{blob_name}' failed ({exc}) — local copy saved, not yet synced")

    store = MetadataStore(data_dir / "projects.json", on_save=lambda: _push_shared_blob("projects.json"))
    system_config_store = SystemConfigStore(
        data_dir / "system_config.json", on_save=lambda: _push_shared_blob("system_config.json")
    )
    program_store = ProgramStore(data_dir / "programs.json", on_save=lambda: _push_shared_blob("programs.json"))
    # local_config.json and github_token.json are per-machine and gitignored
    # — see cache_dir comment above.
    local_config_store = LocalConfigStore(cache_dir / "local_config.json")
    # Workspace root is fixed to the repo's own projects/ folder — there is no
    # UI to point it elsewhere (see interface/settings/common_settings_page.py),
    # so force it here on every launch rather than only defaulting it once.
    forced_workspace_root = str(REPO_ROOT / "projects")
    if local_config_store.workspace_root != forced_workspace_root:
        local_config_store.set_workspace_root(forced_workspace_root)
    hook_registry = HookRegistry()
    git_service = GitService(hooks=hook_registry)
    token_store = TokenStore(cache_dir / "github_token.json")
    # GitHub login now happens in the launcher exe before this process is
    # even spawned (updater.py (UkoreHubLauncher repo) owns the token cache) —
    # just load whatever it already cached, same "presence, not validity"
    # semantics updater.py's own _check_login uses (never calls GitHub to
    # confirm the token still works, only that a login happened at some
    # point on this machine).
    #
    # Mandatory gate: this process refuses to open the main window at all
    # without a cached token. The whole point of moving login into the
    # launcher exe was for it to be the *only* way in — without this check,
    # `python launcher.py` run directly (bypassing UkoreHub.exe entirely)
    # would silently open the full app unauthenticated instead. This is a
    # hard rule, not a soft warning: no MainWindow construction, no plugin
    # discovery, nothing past this point without a token.
    token = token_store.load_token()
    if not token:
        box = QMessageBox(
            QMessageBox.Icon.Critical,
            "Login Required",
            "You must log in to GitHub through UkoreHub.exe before UkoreHub "
            "can open.\n\nRun UkoreHub.exe (the Launcher) and complete the "
            "GitHub login step, then try again.",
        )
        box.exec()
        relaunch_ukorehub_exe(REPO_ROOT)
        sys.exit(1)
    git_service.set_github_token(token)

    apply_theme(app, local_config_store.theme)

    # plugins/core and plugins/repo_internal are both git-tracked and
    # distributed to everyone via self_update.py's whole-tree `git pull`,
    # mirroring how data/programs.json is shared today — both ship bundled
    # with the app, no separate fetch. core is always visible per repo, no
    # per-repo opt-out; repo_internal is hidden per repo unless the repo
    # opts in via Repo.required_plugin_ids
    # (see interface/main_window.py's _apply_plugin_visibility). cache/plugins
    # is different in kind, not just visibility — each entry is its own git
    # clone (own remote/history), gitignored and per-user, fetched/updated on
    # demand only for a repo that requires it; see plugins/README.md.
    # Discovery runs before registry construction so its result (the plugin
    # catalog) can be threaded into the builtin registrations below (Plugins
    # settings tab, repo editor's plugin picker).
    plugins_root = REPO_ROOT / "plugins"
    cache_plugins_root = cache_dir / "plugins"
    (plugins_root / "core").mkdir(parents=True, exist_ok=True)
    (plugins_root / "repo_internal").mkdir(parents=True, exist_ok=True)
    cache_plugins_root.mkdir(parents=True, exist_ok=True)
    discovery = discover_plugins(
        [plugins_root / "core", plugins_root / "repo_internal", cache_plugins_root],
        api_version=PLUGIN_API_VERSION,
    )

    file_opener_registry = FileOpenerRegistry()
    program_launch_registry = ProgramLaunchRegistry()

    section_registry = SectionRegistry()
    settings_tab_registry = SettingsTabRegistry()
    sidebar_footer_action_registry = SidebarFooterActionRegistry()
    register_builtin_settings_tabs(
        settings_tab_registry,
        store=store,
        local_config_store=local_config_store,
        system_config_store=system_config_store,
        program_store=program_store,
        plugin_catalog=discovery.loaded,
        plugin_load_failures=discovery.failures,
    )

    plugin_api = PluginAPI(
        store=store,
        program_store=program_store,
        local_config_store=local_config_store,
        system_config_store=system_config_store,
        git_service=git_service,
        hooks=hook_registry,
        section_registry=section_registry,
        settings_tab_registry=settings_tab_registry,
        file_opener_registry=file_opener_registry,
        program_launch_registry=program_launch_registry,
        sidebar_footer_action_registry=sidebar_footer_action_registry,
        plugins_data_dir=data_dir / "plugins",
        plugins_local_dir=cache_dir / "plugin_local_config",
        cache_dir=cache_dir,
        app_root=REPO_ROOT,
        cloud_sync=cloud_sync,
    )
    # Applied one plugin at a time (rather than one bulk apply_plugins(discovery.loaded, ...)
    # call) so section_registry.keys() can be diffed before/after each
    # plugin's own register(api) call, learning which section(s) it
    # contributed — section_key_to_plugin_id below is what
    # MainWindow._apply_plugin_visibility uses for per-repo Plugin gating
    # (Settings > Repo > Requirements & Plugins).
    plugin_apply_failures: list = []
    section_key_to_plugin_id: dict[str, str] = {}
    for plugin in discovery.loaded:
        keys_before = section_registry.keys()
        plugin_apply_failures += apply_plugins([plugin], plugin_api)
        for key in section_registry.keys() - keys_before:
            section_key_to_plugin_id[key] = plugin.manifest.id

    # Every plugins/core/ plugin is always visible for every repo, no
    # per-repo opt-out (2026-08-04) — anything repo-specific (Maya tools,
    # ...) belongs under plugins/repo_internal/ instead, so what's left in
    # plugins/core/ is meant to be universal app-level functionality (e.g.
    # Project Editor — switching the active repo has no other entry point).
    # See MainWindow._apply_plugin_visibility.
    core_plugin_ids = {plugin.manifest.id for plugin in discovery.loaded if plugin_source(plugin) == "core"}
    # Plugins discovered under plugins/repo_internal/ (bundled with the app)
    # or cache/plugins/ (its own separate git clone) — both opt-in per repo
    # (Repo.required_plugin_ids), see MainWindow._apply_plugin_visibility.
    opt_in_plugin_ids = {
        plugin.manifest.id for plugin in discovery.loaded if plugin_source(plugin) in ("repo_internal", "repo")
    }

    plugin_failures = discovery.failures + plugin_apply_failures
    for failure in plugin_failures:
        print(f"UkoreHub: plugin at '{failure.dir_path}' failed to load: {failure.reason}")

    window = MainWindow(
        store,
        local_config_store,
        program_store,
        git_service,
        token_store,
        cache_dir,
        hook_registry,
        section_registry,
        settings_tab_registry,
        file_opener_registry,
        sidebar_footer_action_registry,
        section_key_to_plugin_id=section_key_to_plugin_id,
        core_plugin_ids=core_plugin_ids,
        opt_in_plugin_ids=opt_in_plugin_ids,
    )
    # MainWindow.__init__ already calls showMaximized() early (so the real
    # UI never flashes unmaximized before it's fully built), but
    # that happens before this window has ever actually been realized on
    # screen. A second showMaximized() call made synchronously here, still
    # before app.exec() has run a single event, is *also* pre-realization —
    # empirically it did not reliably override a clobbered maximized state
    # on Windows (see developer/bug-history/2026-07-20-main-window-not-maximizing.md).
    # QTimer.singleShot(0, ...) queues this call to run right after the
    # event loop actually starts, once the native window exists — the
    # standard, reliable fix for this Qt/Windows quirk.
    QTimer.singleShot(0, window.showMaximized)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
