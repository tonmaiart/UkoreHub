"""UkoreHub entry point.

Bootstraps missing Python package dependencies before importing anything
that needs them, so the user never sees a ModuleNotFoundError.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# CACHE_DIR/DATA_DIR (below) are deliberately allowed to live outside
# REPO_ROOT, so a process spawned from CACHE_DIR/cache/plugins/... (e.g.
# Maya, via maya_launcher's os.environ.copy()) has no relative path back to
# REPO_ROOT. Exported here so such processes can still find the app's own
# code/plugins folder without guessing — see PublishApi/repo_paths.py's
# find_ukorehub_root(). Finding data/ itself is a separate concern now (see
# UKOREHUB_DATA_DIR below) — data/ no longer lives under REPO_ROOT, so
# UKOREHUB_APP_ROOT alone isn't enough for that anymore.
os.environ["UKOREHUB_APP_ROOT"] = str(REPO_ROOT)

# cache/ (per-machine app state), storage/ (cloned workspace repos), and
# data/ (the R2 cloud-synced JSON registry) used to be hardcoded as
# REPO_ROOT-relative — a problem for Update, which replaces this whole app/
# folder (see UkoreHubLauncher's README.md): anything left inside it is
# either wiped or, worse, silently orphaned next to the new copy. Sourced
# from env vars instead so the real launcher exe (UkoreHub.exe, built from
# the separate UkoreHubLauncher repo) can point them at a path outside app/
# before spawning this file — same UKOREHUB_-prefixed convention as
# core/vcs/git_service.py's UKOREHUB_GITHUB_TOKEN. Falls back to a folder
# under the user's own Documents (never REPO_ROOT — see root CLAUDE.md's
# "program folder stays program-only" rule) only for the `python launcher.py`
# direct-invocation dev path, which bypasses UkoreHub.exe entirely and so
# never gets these set.
USER_DATA_DIR = Path.home() / "Documents" / "UkoreHub"
CACHE_DIR = (
    Path(os.environ["UKOREHUB_CACHE_DIR"]) if os.environ.get("UKOREHUB_CACHE_DIR") else USER_DATA_DIR / "cache"
)
STORAGE_DIR = (
    Path(os.environ["UKOREHUB_STORAGE_DIR"]) if os.environ.get("UKOREHUB_STORAGE_DIR") else USER_DATA_DIR / "storage"
)
DATA_DIR = Path(os.environ["UKOREHUB_DATA_DIR"]) if os.environ.get("UKOREHUB_DATA_DIR") else USER_DATA_DIR / "data"
# Re-exported (unlike CACHE_DIR/STORAGE_DIR) so a Maya session spawned later
# from this running app inherits the *resolved* path regardless of whether
# it came from the env var above or the Documents fallback — same treatment
# UKOREHUB_APP_ROOT gets above. This is what Maya-side repo_paths.py clones
# should switch to reading instead of assuming data/ sits under
# UKOREHUB_APP_ROOT (not yet done for any of them — separate follow-up).
os.environ["UKOREHUB_DATA_DIR"] = str(DATA_DIR)

REQUIRED_PACKAGES = [
    ("PySide6", "PySide6>=6.7,<7.0"),
    ("keyring", "keyring>=24.0"),
    ("boto3", "boto3>=1.36.0"),
]

GIT_DOWNLOAD_URL = "https://github.com/git-for-windows/git/releases/download/v2.55.0.windows.3/Git-2.55.0.3-64-bit.exe"


def ensure_dependencies() -> None:
    for import_name, pip_spec in REQUIRED_PACKAGES:
        try:
            # find_spec on a dotted name tries to import the parent package
            # first — if that parent isn't installed at all yet, it raises
            # ModuleNotFoundError instead of just returning None, so that
            # case needs its own catch too.
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


def _build_cloud_sync(data_dir: Path, appdata_dir: Path):
    """Best-effort: returns None (cloud sync disabled, the shared stores
    stay purely local) whenever the shared R2 credentials aren't available
    on this machine — either the UKOREHUB_R2_* env vars are missing
    (always true for the `python launcher.py` direct-invocation dev path,
    which bypasses UkoreHubLauncher.exe and its env-var injection — see
    developer/launcher/launcher_build/updater.py's _launch()) or no bucket
    name can be found. There is no per-user login step anymore — a single
    shared key means an artist either has full read/write access or the
    app falls back to local-only, nothing in between.

    Reads the bucket name off the raw local system_config.json rather than
    through SystemConfigStore, since that store is itself one of the
    things this function ends up syncing — which creates a bootstrap
    problem on a machine that has never run UkoreHub before:
    data/system_config.json is gitignored (see .gitignore's comment), so a
    fresh clone has no local copy yet, and the bucket name needed to pull
    the real one lives inside it. appdata/system_config.default.json
    (tracked in git, see developer/app/docs/data-layout.md — deliberately kept out of
    data/, which is reserved for cloud-synced files only, including by the
    Maya-side scripts under cache/plugins/ clones that hardcode data/
    paths directly) breaks that cycle — same "not meaningfully secret for
    a distributed desktop app" reasoning already applied to
    github_client_id. Only consulted when the local file is
    missing/incomplete; the pull() below then overwrites
    data/system_config.json with the real cloud copy, so later runs never
    need the fallback again."""
    account_id = os.environ.get("UKOREHUB_R2_ACCOUNT_ID")
    access_key_id = os.environ.get("UKOREHUB_R2_ACCESS_KEY_ID")
    secret_access_key = os.environ.get("UKOREHUB_R2_SECRET_ACCESS_KEY")
    if not all([account_id, access_key_id, secret_access_key]):
        return None

    system_config_path = data_dir / "system_config.json"
    config = {}
    if system_config_path.exists():
        config = json.loads(system_config_path.read_text(encoding="utf-8"))
    bucket_name = config.get("r2_bucket_name") or os.environ.get("UKOREHUB_R2_BUCKET_NAME")
    if not bucket_name:
        default_path = appdata_dir / "system_config.default.json"
        if not default_path.exists():
            return None
        config = json.loads(default_path.read_text(encoding="utf-8"))
        bucket_name = config.get("r2_bucket_name")
        if not bucket_name:
            return None

    from core.vcs.cloud_sync import R2JsonSync

    return R2JsonSync(account_id, access_key_id, secret_access_key, bucket_name)


def main() -> None:
    ensure_dependencies()

    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication, QMessageBox

    # Fractional Windows display scaling (125%/150%/175%) can leave Qt's
    # painted widget positions and the mouse-event coordinates Windows
    # delivers rounded to slightly different pixel grids — on some
    # machines this shows up as checkboxes/list rows that render fine but
    # don't register clicks. Rounding the scale factor to a whole number
    # keeps both grids aligned.
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Round)
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

    from core_api import (
        ConflictError,
        FileOpenerRegistry,
        UkoreCore,
        apply_plugins,
        discover_plugins,
        migrate_legacy_programs,
        plugin_source,
        read_project_ids,
        relaunch_ukorehub_exe,
    )
    from interface_api import (
        MainWindow,
        QtLogHandler,
        apply_theme,
        configure_app_logging,
        register_builtin_settings_tabs,
    )
    from plugin_api import (
        PLUGIN_API_VERSION,
        NotificationRegistry,
        PluginAPI,
        ProgramLaunchRegistry,
        SectionRegistry,
        SettingsTabRegistry,
        SidebarFooterActionRegistry,
        UIRegistryManager,
    )

    # Constructed as early as possible (right after these imports resolve,
    # before anything below has a chance to log) so every logging.getLogger(...)
    # call anywhere in the app — including the cloud-bootstrap block right
    # below — shows up live in DebugConsole.
    qt_log_handler = QtLogHandler(max_entries=1000)
    configure_app_logging(qt_log_handler)

    data_dir = DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    # data/assets/ holds thumbnails/program_icons — like every other file
    # under data/, these are just a local cache of an R2 blob (pulled
    # lazily per-file on first read instead of eagerly at launch, since
    # unlike the JSON stores there's no small fixed set of them to pull
    # upfront — see MetadataStore's on_asset_upload/on_asset_missing and
    # _push_asset/_pull_asset below). See developer/app/docs/data-layout.md.
    assets_dir = data_dir / "assets"
    # appdata/ holds the git-tracked static files data/ itself doesn't own —
    # bootstrap defaults and examples that are never cloud-synced and never
    # written by the running app. Kept out of data/ so data/ is unambiguously
    # "cloud-synced JSON only", matching what the Maya-side scripts under
    # cache/plugins/ clones already assume when they hardcode data/ paths
    # directly (they can't import PluginAPI, so they duplicate this
    # assumption rather than reading it from anywhere). See developer/app/docs/data-layout.md.
    appdata_dir = REPO_ROOT / "appdata"
    appdata_dir.mkdir(exist_ok=True)
    # cache/ is where every per-machine, gitignored file lives now (not
    # data/) — it's already excluded wholesale from UkoreHub.exe (git-
    # tracked) and from developer/commit-main.ps1's release publish, so
    # anything placed here can never accidentally ship in a release the way
    # a stray copy of data/ would. See cache/README.md. Location comes from
    # CACHE_DIR (module-level, above) — not necessarily under REPO_ROOT.
    cache_dir = CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    cloud_sync_logger = logging.getLogger("CloudSync")

    # projects.json, system_config.json, and programs.json are shared
    # studio-wide via Cloudflare R2 (core/vcs/cloud_sync.py), not git —
    # pull whatever's newest before constructing the stores that read them,
    # and wire on_save so every local edit pushes straight back up.
    #
    # projects.json is itself just a lightweight index now (id/name only) —
    # the real per-project data lives in projects/<id>.json blobs (see
    # core/storage/metadata_store.py's MetadataStore, developer/app/docs/data-layout.md). Once
    # the index is pulled, pull every project blob it references too; a
    # still-old-shape index (schema_version < 2, repos embedded) means
    # nothing has migrated yet, so read_project_ids returns None and
    # there's nothing per-project to pull — MetadataStore.load()'s one-time
    # migration handles that locally and pushes the new blobs itself once
    # constructed below.
    cloud_sync = _build_cloud_sync(data_dir, appdata_dir)
    if cloud_sync is None:
        print("UkoreHub: cloud sync not configured on this machine — shared data stays local-only.")
        cloud_sync_logger.warning("not configured on this machine — shared data stays local-only")
    else:
        try:
            for blob_name in ("projects.json", "programs.json", "system_config.json"):
                cloud_sync.pull(blob_name, data_dir / blob_name)
                cloud_sync_logger.info(f"pulled '{blob_name}'")
            project_ids = read_project_ids(data_dir / "projects.json")
            if project_ids is not None:
                for project_id in project_ids:
                    blob_name = f"projects/{project_id}.json"
                    cloud_sync.pull(blob_name, data_dir / "projects" / f"{project_id}.json")
                    cloud_sync_logger.info(f"pulled '{blob_name}'")
        except Exception as exc:
            # Revoked/rotated R2 key, no network, bucket not reachable,
            # etc. — never block the app from opening over a cloud problem;
            # fall back to local-only for this run, same as "not configured
            # at all".
            print(f"UkoreHub: cloud sync unavailable this run ({exc}) — shared data stays local-only.")
            cloud_sync_logger.warning(f"unavailable this run ({exc}) — shared data stays local-only")
            cloud_sync = None

    def _push_shared_blob(blob_name: str) -> None:
        if cloud_sync is None:
            return
        try:
            cloud_sync.push(blob_name, data_dir / blob_name)
            cloud_sync_logger.info(f"pushed '{blob_name}'")
        except ConflictError as exc:
            # Meaningful to the caller (a real conflicting edit elsewhere) —
            # let it propagate so the UI can tell the artist and reload.
            cloud_sync_logger.warning(f"push of '{blob_name}' conflicted ({exc}) — reloaded latest")
            raise
        except Exception as exc:
            # Timeout, no network, revoked login, etc. — the local save
            # already succeeded (on_save fires after _atomic_write), so
            # don't fail the whole edit over a transient cloud problem;
            # just warn. The next successful save catches this file back up.
            print(f"UkoreHub: cloud push of '{blob_name}' failed ({exc}) — local copy saved, not yet synced.")
            cloud_sync_logger.warning(f"push of '{blob_name}' failed ({exc}) — local copy saved, not yet synced")

    def _delete_shared_blob(blob_name: str) -> None:
        # Only used by MetadataStore.delete_project, to clean up a removed
        # project's now-orphaned projects/<id>.json blob. Same
        # never-fail-the-local-edit-over-a-transient-cloud-problem posture as
        # _push_shared_blob above — the project is already gone locally
        # either way.
        if cloud_sync is None:
            return
        try:
            cloud_sync.delete(blob_name)
            cloud_sync_logger.info(f"deleted '{blob_name}'")
        except Exception as exc:
            print(f"UkoreHub: cloud delete of '{blob_name}' failed ({exc}) — it may linger in the bucket.")
            cloud_sync_logger.warning(f"delete of '{blob_name}' failed ({exc}) — it may linger in the bucket")

    def _push_asset(blob_name: str, local_path: Path) -> None:
        # Thumbnails/program icons: last-write-wins is fine (no structural
        # data to lose the way a conflicting JSON edit would), so unlike
        # _push_shared_blob this swallows ConflictError too instead of
        # propagating it — the artist's own local upload already succeeded
        # and is what they expect to see; whoever's push "lost" is still
        # safely in the bucket for anyone else who pulls it.
        if cloud_sync is None:
            return
        try:
            cloud_sync.push(blob_name, local_path)
            cloud_sync_logger.info(f"pushed asset '{blob_name}'")
        except Exception as exc:
            print(f"UkoreHub: cloud push of asset '{blob_name}' failed ({exc}) — local copy saved, not yet synced.")
            cloud_sync_logger.warning(f"push of asset '{blob_name}' failed ({exc}) — local copy saved, not yet synced")

    def _pull_asset(blob_name: str, local_path: Path) -> None:
        # Best-effort lazy pull, called by resolve_thumbnail_path/
        # resolve_program_icon_path when the local file is missing. Silent
        # on failure either way (no network, or genuinely nobody's
        # uploaded this blob yet) — the caller just falls back to "no
        # image", the same as today when no filename is set at all.
        if cloud_sync is None:
            return
        try:
            cloud_sync.pull(blob_name, local_path)
            cloud_sync_logger.info(f"pulled asset '{blob_name}'")
        except Exception as exc:
            cloud_sync_logger.warning(f"pull of asset '{blob_name}' failed ({exc}) — leaving it unset")

    core = UkoreCore(
        data_dir=data_dir,
        cache_dir=cache_dir,
        assets_dir=assets_dir,
        on_metadata_save=_push_shared_blob,
        on_metadata_delete=_delete_shared_blob,
        on_metadata_asset_upload=_push_asset,
        on_metadata_asset_missing=_pull_asset,
        on_system_config_save=lambda: _push_shared_blob("system_config.json"),
        debug_log_handler=qt_log_handler,
    )
    store = core.metadata
    system_config_store = core.system_config
    local_config_store = core.local_config
    hook_registry = core.hooks
    git_service = core.git
    token_store = core.github_tokens
    # programs.json is a retired studio-wide Program Database — Program is
    # now owned per-Project (Project.programs, core/models.py) instead.
    # Still pulled above (fixed 3-blob loop) so this migration reads the
    # latest cloud copy; nothing writes it back afterward, and it's
    # deliberately left in place rather than deleted — see
    # migrate_legacy_programs's own docstring.
    migrate_legacy_programs(store, data_dir / "programs.json")
    # Workspace root is fixed to STORAGE_DIR (module-level, above — not
    # necessarily under REPO_ROOT) — there is no UI to point it elsewhere (see
    # interface/settings/common_settings_page.py), so force it here on every
    # launch rather than only defaulting it once.
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    forced_workspace_root = str(STORAGE_DIR)
    if local_config_store.workspace_root != forced_workspace_root:
        local_config_store.set_workspace_root(forced_workspace_root)
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

    # Project must be fixed for the whole session before plugins/MainWindow
    # are constructed — every page downstream (Program Database, Software
    # Linker, Project Editor's Viewgraph, ...) now assumes
    # local_config_store.active_project_id already points at a real
    # project, with no in-app way to change it to a *different* one at
    # all — UkoreHub is designed to launch into one project only, so a
    # different project means a full relaunch back through this same gate
    # (there used to be a "Switch Project..." button in Settings that did
    # this in-app via interface/main_window.py's _request_switch_project —
    # removed 2026-09-01 along with the rest of
    # plugins/core/project_editor/project_settings_page.py, per the user's
    # own call that switching wasn't the app's job to begin with). Skipped
    # entirely — no dialog shown — when the remembered active_project_id
    # already resolves, or when there's at most one project to begin with
    # (nothing to actually choose), so an ordinary day-to-day launch stays
    # a single click through the GitHub gate above, same as before this
    # existed.
    existing_project_ids = {project.id for project in store.list_projects()}
    if local_config_store.active_project_id not in existing_project_ids:
        if len(existing_project_ids) <= 1:
            local_config_store.set_active_project(next(iter(existing_project_ids), None))
        else:
            from interface_api import ProjectSelectorDialog

            selector = ProjectSelectorDialog(store.list_projects())
            if not selector.exec():
                sys.exit(0)
            local_config_store.set_active_project(selector.selected_project_id())

    # Reconcile Repo.status against disk for the active project — picks up
    # a repo folder an artist copy-pasted into the workspace root directly
    # (see core/storage/metadata_store.py's refresh_statuses_from_disk)
    # instead of leaving it showing stale/"not_cloned" until the artist
    # happens to switch to that repo and trigger a Sync.
    if local_config_store.active_project_id:
        store.refresh_statuses_from_disk(
            local_config_store.active_project_id, local_config_store.workspace_root, git_service
        )

    # plugins/core is git-tracked and distributed to everyone via
    # self_update.py's whole-tree `git pull`, mirroring how
    # data/programs.json is shared today — ships bundled with the app, no
    # separate fetch, always visible per repo, no per-repo opt-out.
    # cache/plugins is different in kind, not just visibility — each entry
    # is its own git clone (own remote/history), gitignored and per-user,
    # fetched/updated on demand only for a repo that requires it (opts in
    # via Repo.required_plugin_ids, see
    # interface/main_window.py's _apply_plugin_visibility); see
    # developer/app/docs/plugins-guide.md.
    # Discovery runs before registry construction so its result (the plugin
    # catalog) can be threaded into the builtin registrations below (Plugins
    # settings tab, repo editor's plugin picker).
    plugins_root = REPO_ROOT / "plugins"
    cache_plugins_root = cache_dir / "plugins"
    (plugins_root / "core").mkdir(parents=True, exist_ok=True)
    cache_plugins_root.mkdir(parents=True, exist_ok=True)
    discovery = discover_plugins(
        [plugins_root / "core", cache_plugins_root],
        api_version=PLUGIN_API_VERSION,
    )

    # "repo" (cache/plugins/, each its own separate git clone — see
    # plugin_source() below) plugins are far more likely to break than a
    # bundled "core" one, so their load/register results get their own
    # DebugConsole source — same logger name plugins/core/project_editor/'s
    # own plugin.py already uses for its External Plugins sync status
    # (kept as "ExternalPluginManager" even after that plugin was merged
    # into project_editor 2026-09-01, for DebugConsole log continuity —
    # see that file's own comment), so both show up together.
    plugin_loader_logger = logging.getLogger("PluginLoader")
    external_plugin_logger = logging.getLogger("ExternalPluginManager")

    def _is_repo_plugin_dir(dir_path: Path) -> bool:
        # Same check as core/extensibility/loader.py's plugin_source(), just
        # against a bare dir_path (PluginLoadFailure has no DiscoveredPlugin
        # to call plugin_source() on — discovery can fail before a manifest
        # is even read).
        parent = dir_path.parent
        return parent.name == "plugins" and parent.parent.name == "cache"

    for failure in discovery.failures:
        logger = external_plugin_logger if _is_repo_plugin_dir(failure.dir_path) else plugin_loader_logger
        logger.error(f"plugin at '{failure.dir_path}' failed to load: {failure.reason}")

    registries = UIRegistryManager(
        sections=SectionRegistry(),
        settings_tabs=SettingsTabRegistry(),
        file_openers=FileOpenerRegistry(),
        program_launchers=ProgramLaunchRegistry(),
        sidebar_footer_actions=SidebarFooterActionRegistry(),
        notifications=NotificationRegistry(),
    )
    register_builtin_settings_tabs(
        registries.settings_tabs,
        local_config_store=local_config_store,
        system_config_store=system_config_store,
        plugin_catalog=discovery.loaded,
        plugin_load_failures=discovery.failures,
    )

    plugin_api = PluginAPI(
        core=core,
        registries=registries,
        plugins_data_dir=data_dir / "plugins",
        plugins_local_dir=cache_dir / "plugin_local_config",
        cache_dir=cache_dir,
        app_root=REPO_ROOT,
        cloud_sync=cloud_sync,
        plugin_catalog=discovery.loaded,
    )
    # Applied one plugin at a time (rather than one bulk apply_plugins(discovery.loaded, ...)
    # call) so registries.sections.keys() can be diffed before/after each
    # plugin's own register(api) call, learning which section(s) it
    # contributed — section_key_to_plugin_id below is what
    # MainWindow._apply_plugin_visibility uses for per-repo Plugin gating
    # (Settings > Repo > Requirements & Plugins).
    section_key_to_plugin_id: dict[str, str] = {}
    for plugin in discovery.loaded:
        keys_before = registries.sections.keys()
        apply_result = apply_plugins([plugin], plugin_api)
        logger = external_plugin_logger if plugin_source(plugin) == "repo" else plugin_loader_logger
        if apply_result:
            logger.error(f"{plugin.manifest.id}: register(api) failed — {apply_result[0].reason}")
        else:
            logger.info(f"{plugin.manifest.id}: registered successfully")
        for key in registries.sections.keys() - keys_before:
            section_key_to_plugin_id[key] = plugin.manifest.id

    # Every plugins/core/ plugin is always visible for every repo, no
    # per-repo opt-out (2026-08-04) — anything repo-specific (Maya tools,
    # ...) belongs under cache/plugins/ instead, so what's left in
    # plugins/core/ is meant to be universal app-level functionality (e.g.
    # Project Editor — switching the active repo has no other entry point).
    # See MainWindow._apply_plugin_visibility.
    core_plugin_ids = {plugin.manifest.id for plugin in discovery.loaded if plugin_source(plugin) == "core"}
    # Plugins discovered under cache/plugins/ (each its own separate git
    # clone) — opt-in per repo (Repo.required_plugin_ids), see
    # MainWindow._apply_plugin_visibility.
    opt_in_plugin_ids = {
        plugin.manifest.id for plugin in discovery.loaded if plugin_source(plugin) == "repo"
    }

    window = MainWindow(
        core,
        cache_dir,
        registries,
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
    # on Windows (see the ukorehub-interface skill).
    # QTimer.singleShot(0, ...) queues this call to run right after the
    # event loop actually starts, once the native window exists — the
    # standard, reliable fix for this Qt/Windows quirk.
    QTimer.singleShot(0, window.showMaximized)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
