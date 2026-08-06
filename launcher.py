"""UkoreHub entry point.

Bootstraps missing Python package dependencies before importing anything
that needs them, so the user never sees a ModuleNotFoundError.
"""
from __future__ import annotations

import importlib.util
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
]

GIT_DOWNLOAD_URL = "https://github.com/git-for-windows/git/releases/download/v2.55.0.windows.3/Git-2.55.0.3-64-bit.exe"


def ensure_dependencies() -> None:
    for import_name, pip_spec in REQUIRED_PACKAGES:
        if importlib.util.find_spec(import_name) is not None:
            continue
        print(f"UkoreHub: installing missing dependency '{pip_spec}'...")
        subprocess.run([sys.executable, "-m", "pip", "install", pip_spec], check=True)


# Presence checks only — no auto-install. UkoreHub.exe (developer/packaging/
# updater.py) already checks/updates before this file is ever spawned; these
# only matter for the `python launcher.py` direct-invocation dev path, which
# bypasses that exe entirely.


def check_git_prerequisite() -> bool:
    return shutil.which("git") is not None


def check_git_lfs_prerequisite() -> bool:
    return shutil.which("git-lfs") is not None


def main() -> None:
    ensure_dependencies()

    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication, QMessageBox

    app = QApplication(sys.argv)
    # developer/packaging/icon.ico is only baked into UkoreHub.exe itself (via
    # PyInstaller's --icon) — that thin exe just spawns `pythonw
    # launcher.py` detached and exits (see developer/packaging/exe_entry.py), so the
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

    from core.extensibility.file_opener import FileOpenerRegistry
    from core.extensibility.hooks import HookRegistry
    from core.extensibility.loader import apply_plugins, discover_plugins, plugin_source
    from core.git_service import GitService
    from core.github.token_store import TokenStore
    from core.program_store import ProgramStore
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

    # projects.json, system_config.json, and programs.json are shared/tracked
    # in this repo; local_config.json and github_token.json are per-machine
    # and gitignored.
    store = MetadataStore(data_dir / "projects.json")
    system_config_store = SystemConfigStore(data_dir / "system_config.json")
    program_store = ProgramStore(data_dir / "programs.json")
    local_config_store = LocalConfigStore(data_dir / "local_config.json")
    # Workspace root is fixed to the repo's own projects/ folder — there is no
    # UI to point it elsewhere (see interface/settings/common_settings_page.py),
    # so force it here on every launch rather than only defaulting it once.
    forced_workspace_root = str(REPO_ROOT / "projects")
    if local_config_store.workspace_root != forced_workspace_root:
        local_config_store.set_workspace_root(forced_workspace_root)
    hook_registry = HookRegistry()
    git_service = GitService(hooks=hook_registry)
    token_store = TokenStore(data_dir / "github_token.json")
    # GitHub login now happens in the launcher exe before this process is
    # even spawned (developer/packaging/updater.py owns the token cache) —
    # just load whatever it already cached, same "presence, not validity"
    # semantics the old in-app LoginGate.restore_session_state() used. If
    # this is None (e.g. running `python launcher.py` directly without ever
    # going through the launcher exe first), GitService simply stays
    # unauthenticated — private-repo git operations fail with a normal auth
    # error, same as before anyone had ever logged in.
    token = token_store.load_token()
    if token:
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
    cache_plugins_root = REPO_ROOT / "cache" / "plugins"
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
        git_service=git_service,
        hooks=hook_registry,
        section_registry=section_registry,
        settings_tab_registry=settings_tab_registry,
        file_opener_registry=file_opener_registry,
        program_launch_registry=program_launch_registry,
        sidebar_footer_action_registry=sidebar_footer_action_registry,
        plugins_data_dir=data_dir / "plugins",
        app_root=REPO_ROOT,
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
