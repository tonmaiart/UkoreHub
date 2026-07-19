"""UkoreHub entry point.

Bootstraps missing Python package dependencies before importing anything
that needs them, so the user never sees a ModuleNotFoundError.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REQUIRED_PACKAGES = [
    ("PySide6", "PySide6>=6.7,<7.0"),
    ("keyring", "keyring>=24.0"),
]


def ensure_dependencies() -> None:
    for import_name, pip_spec in REQUIRED_PACKAGES:
        if importlib.util.find_spec(import_name) is not None:
            continue
        print(f"UkoreHub: installing missing dependency '{pip_spec}'...")
        subprocess.run([sys.executable, "-m", "pip", "install", pip_spec], check=True)


def _refresh_path_from_registry() -> None:
    """A winget install that just completed updates the registry, not this
    already-running process's environment (env vars are only inherited at
    process creation) — merge the machine + user PATH from the registry into
    os.environ so a just-installed binary's shutil.which() can find it
    without restarting UkoreHub."""
    if sys.platform != "win32":
        return
    import winreg

    def _read(hive: int, subkey: str) -> str:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                value, _ = winreg.QueryValueEx(key, "Path")
                return value
        except OSError:
            return ""

    machine_path = _read(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
    user_path = _read(winreg.HKEY_CURRENT_USER, "Environment")
    combined = ";".join(p for p in (machine_path, user_path, os.environ.get("PATH", "")) if p)
    if combined:
        os.environ["PATH"] = combined


def _winget_install(package_id: str, display_name: str) -> bool:
    """Best-effort silent install via winget (ships by default on Windows
    10/11) — never raises, so callers can fall back to a manual-install
    message. Returns whether winget itself ran the install successfully;
    callers still need to re-check shutil.which() afterwards since a
    successful install doesn't guarantee this process can see the new PATH
    entry (see _refresh_path_from_registry)."""
    if sys.platform != "win32" or shutil.which("winget") is None:
        return False
    print(f"UkoreHub: '{display_name}' not found — installing via winget...")
    try:
        subprocess.run(
            [
                "winget", "install", "--id", package_id, "-e",
                "--silent", "--accept-package-agreements", "--accept-source-agreements",
            ],
            check=True,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"UkoreHub: winget install of '{display_name}' failed: {exc}")
        return False
    _refresh_path_from_registry()
    return True


def check_git_prerequisite() -> bool:
    if shutil.which("git") is not None:
        return True
    if not _winget_install("Git.Git", "git"):
        return False
    return shutil.which("git") is not None


def check_git_lfs_prerequisite() -> bool:
    if shutil.which("git-lfs") is not None:
        return True
    if not _winget_install("GitHub.GitLFS", "git-lfs"):
        return False
    return shutil.which("git-lfs") is not None


def main() -> None:
    ensure_dependencies()

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication, QMessageBox

    app = QApplication(sys.argv)
    # packaging/icon.ico is only baked into UkoreHub.exe itself (via
    # PyInstaller's --icon) — that thin exe just spawns `pythonw
    # launcher.py` detached and exits (see packaging/exe_entry.py), so the
    # actual GUI process is plain python(w).exe and would otherwise show
    # Windows' generic Python icon in the taskbar/title bar unless the Qt
    # app sets its own window icon here.
    icon_path = REPO_ROOT / "packaging" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    if not check_git_prerequisite():
        QMessageBox.critical(
            None,
            "Git Not Found",
            "UkoreHub requires 'git' to be installed and available on your PATH.\n"
            "Automatic install via winget wasn't available or didn't succeed — "
            "please install git yourself and restart UkoreHub.",
        )
        sys.exit(1)

    if not check_git_lfs_prerequisite():
        QMessageBox.warning(
            None,
            "git-lfs Not Found",
            "'git-lfs' was not found on your PATH, and automatic install via "
            "winget wasn't available or didn't succeed.\n"
            "Some repos may require it — you can continue, but LFS-tracked files "
            "may not sync correctly.",
        )

    from core.addon_store import AddonMetadataStore
    from core.extensibility.file_opener import FileOpenerRegistry
    from core.extensibility.hooks import HookRegistry
    from core.extensibility.loader import apply_plugins, discover_plugins
    from core.git_service import GitService
    from core.github.token_store import TokenStore
    from core.program_store import ProgramStore
    from core.store import LocalConfigStore, MetadataStore, SystemConfigStore
    from interface.builtin_sections import register_builtin_sections
    from interface.builtin_settings_tabs import register_builtin_settings_tabs
    from interface.main_window import MainWindow
    from interface.plugin_api import PLUGIN_API_VERSION, PluginAPI
    from interface.repo_addon_panel_registry import RepoAddonPanelRegistry
    from interface.section_registry import SectionRegistry
    from interface.settings_tab_registry import SettingsTabRegistry
    from interface.theme_apply import apply_theme

    data_dir = REPO_ROOT / "data"
    data_dir.mkdir(exist_ok=True)

    # projects.json, system_config.json, programs.json, and addon_settings.json
    # are shared/tracked in this repo; local_config.json and github_token.json
    # are per-machine and gitignored.
    store = MetadataStore(data_dir / "projects.json")
    system_config_store = SystemConfigStore(data_dir / "system_config.json")
    program_store = ProgramStore(data_dir / "programs.json")
    addon_store = AddonMetadataStore(data_dir / "addon_settings.json")
    local_config_store = LocalConfigStore(data_dir / "local_config.json")
    # Workspace root is fixed to the repo's own projects/ folder — there is no
    # UI to point it elsewhere (see interface/settings/common_settings_page.py
    # and interface/login/login_overlay.py), so force it here on every launch
    # rather than only defaulting it once.
    forced_workspace_root = str(REPO_ROOT / "projects")
    if local_config_store.workspace_root != forced_workspace_root:
        local_config_store.set_workspace_root(forced_workspace_root)
    hook_registry = HookRegistry()
    git_service = GitService(hooks=hook_registry)
    token_store = TokenStore(data_dir / "github_token.json")

    apply_theme(app, local_config_store.theme)

    # plugins/studio is git-tracked and distributed to everyone via
    # self_update.py's whole-tree `git pull`, mirroring how data/programs.json
    # is shared today; plugins/local is gitignored, per-machine/experimental.
    # Discovery runs before registry construction so its result (the plugin
    # catalog) can be threaded into the builtin registrations below (Plugins
    # settings tab, repo editor's plugin picker, Repo About).
    plugins_root = REPO_ROOT / "plugins"
    (plugins_root / "studio").mkdir(parents=True, exist_ok=True)
    (plugins_root / "local").mkdir(parents=True, exist_ok=True)
    discovery = discover_plugins([plugins_root / "studio", plugins_root / "local"], api_version=PLUGIN_API_VERSION)

    # add-on/ is a single flat, git-tracked catalog of repo-scoped add-ons
    # (Repo.enabled_addon_ids) — distinct from the always-on plugins/
    # catalog above. Same discovery mechanism, no studio/local split.
    add_on_root = REPO_ROOT / "add-on"
    add_on_root.mkdir(parents=True, exist_ok=True)
    addon_discovery = discover_plugins([add_on_root], api_version=PLUGIN_API_VERSION)

    repo_addon_panel_registry = RepoAddonPanelRegistry()
    file_opener_registry = FileOpenerRegistry()

    section_registry = SectionRegistry()
    register_builtin_sections(
        section_registry,
        store=store,
        local_config_store=local_config_store,
        git_service=git_service,
        program_store=program_store,
        addon_store=addon_store,
        repo_addon_panel_registry=repo_addon_panel_registry,
        addon_catalog=addon_discovery.loaded,
    )
    settings_tab_registry = SettingsTabRegistry()
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
        repo_addon_panel_registry=repo_addon_panel_registry,
        file_opener_registry=file_opener_registry,
        plugins_data_dir=data_dir / "plugins",
        app_root=REPO_ROOT,
        addon_store=addon_store,
        addon_catalog=addon_discovery.loaded,
    )
    # Applied one plugin at a time (rather than one bulk apply_plugins(discovery.loaded, ...)
    # call) so section_registry.keys() can be diffed before/after each
    # plugin's own register(api) call, learning which section(s) it
    # contributed — section_key_to_plugin_id below is what
    # MainWindow._apply_plugin_visibility uses for per-repo Plugin gating
    # (Settings > Repo > Enable Plugin). add-on/ is untouched — that catalog
    # keeps its existing enabled_addon_ids gating instead.
    plugin_apply_failures: list = []
    section_key_to_plugin_id: dict[str, str] = {}
    for plugin in discovery.loaded:
        keys_before = section_registry.keys()
        plugin_apply_failures += apply_plugins([plugin], plugin_api)
        for key in section_registry.keys() - keys_before:
            section_key_to_plugin_id[key] = plugin.manifest.id

    # Plugins flagged manifest.json "core": true (e.g. Project Editor —
    # switching the active repo has no other entry point) must never be
    # hidden by a repo's restricted active_plugin_ids allowlist — see
    # MainWindow._apply_plugin_visibility.
    core_plugin_ids = {plugin.manifest.id for plugin in discovery.loaded if plugin.manifest.core}

    plugin_failures = (
        discovery.failures
        + addon_discovery.failures
        + plugin_apply_failures
        + apply_plugins(addon_discovery.loaded, plugin_api)
    )
    for failure in plugin_failures:
        print(f"UkoreHub: plugin at '{failure.dir_path}' failed to load: {failure.reason}")

    window = MainWindow(
        store,
        local_config_store,
        system_config_store,
        program_store,
        git_service,
        token_store,
        hook_registry,
        section_registry,
        settings_tab_registry,
        file_opener_registry,
        section_key_to_plugin_id=section_key_to_plugin_id,
        core_plugin_ids=core_plugin_ids,
    )
    # MainWindow.__init__ already calls showMaximized() early (so the login
    # gate itself never flashes unmaximized before real content loads), but
    # that happens before this window has ever actually been realized on
    # screen — a plain window.show() here can silently leave it at its
    # pre-realization "normal" geometry instead of a true maximized one on
    # Windows. Calling showMaximized() again here, as the last step right
    # before the window is actually shown, is what makes it stick.
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
