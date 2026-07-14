from __future__ import annotations

import os
import subprocess
from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from core.exceptions import NotFoundError
from interface.settings_tab_registry import CATEGORY_REPO, SettingsTabSpec
from plugins.studio.maya_launcher.repo_tools_store import RepoToolsStore
from plugins.studio.maya_launcher.settings_page import MayaLauncherSettingsPage
from plugins.studio.maya_launcher.tools import ANY_VERSION, build_contributions

ADDON_ID = "maya_launcher"
# Convention-only string match with plugins/studio/software_linker/plugin.py
# — both resolve to the same data/plugins/local/software_linker.json via
# PluginConfigStore, no coupling API needed.
SOFTWARE_LINKER_PLUGIN_ID = "software_linker"

MAYA_FILE_EXTENSIONS = [".ma", ".mb"]

PLUGIN_DIR = Path(__file__).resolve().parent


def _maya_programs_for_repo(api, repo):
    """Every Program the repo requires whose name contains "maya" — resolved
    via repo.required_program_ids, same lookup used by both the settings
    page's link-status readout and the file opener below."""
    programs = []
    for program_id in repo.required_program_ids:
        try:
            program = api.programs.get_program(program_id)
        except NotFoundError:
            continue
        if "maya" in program.name.lower():
            programs.append(program)
    return programs


def _repo_root_path(api, repo) -> Path:
    """The repo's cloned root folder on this machine — where its
    workspace.mel always lives, per studio convention, so this is what gets
    passed to Maya's `setProject`. `repo.local_path` is stored relative to
    the workspace root (see core/store.py's `add_repo`), the same join every
    other page does (e.g. repo_about_page.py via core/paths.py's
    resolve_repo_path)."""
    return Path(api.local_config.workspace_root) / repo.local_path


def _mel_string(path: Path) -> str:
    """A filesystem path as a MEL string literal — forward slashes (MEL's
    own convention, sidesteps backslash-escaping ambiguity) with internal
    double-quotes escaped defensively."""
    return str(path).replace("\\", "/").replace('"', '\\"')


def _set_project_and_open_command(repo_root: Path, scene_path: Path) -> str:
    """Pure, testable: the MEL passed to Maya's `-command` flag. Uses the
    real `setProject` MEL command rather than the `-proj` CLI flag — `-proj`'s
    interactive-Maya support turned out unreliable in practice (a repo whose
    workspace.mel demonstrably sits at repo root still hit Maya's own "Path
    does not exist" project-restore dialog), whereas `setProject` is Maya's
    own always-available, directly-documented command for this. Opening the
    scene via `file -open -force` in the same command (instead of passing it
    as a positional CLI arg) guarantees setProject runs first."""
    return f'setProject "{_mel_string(repo_root)}"; file -open -force "{_mel_string(scene_path)}";'


def _build_maya_env(base_env: dict, contributions: dict, maya_version: str) -> dict:
    """Pure, testable: returns a new env dict with each enabled tool's paths
    prepended (not replaced) onto the env var it targets — prepending keeps
    whatever the artist's own Maya/mGear install already put there.
    `contributions` is tools.build_contributions()'s
    {tool_id: {var_name: {"*": [...], "<version>": [...]}}} shape;
    `maya_version` selects which version-specific entries also apply, on top
    of every "*" entry. Iterates tool_ids sorted for deterministic env var
    ordering across runs."""
    env = dict(base_env)
    for tool_id in sorted(contributions):
        for var_name, by_version in contributions[tool_id].items():
            paths = list(by_version.get(ANY_VERSION, [])) + list(by_version.get(maya_version, []))
            for new_entry in paths:
                existing = env.get(var_name)
                env[var_name] = f"{new_entry}{os.pathsep}{existing}" if existing else new_entry
    return env


def register(api) -> None:
    tools_store = RepoToolsStore(api.plugin_config_store(ADDON_ID, shared=True))

    def open_maya_file(path: Path, repo) -> bool:
        linked = api.plugin_config_store(SOFTWARE_LINKER_PLUGIN_ID, shared=False)
        maya_exe = None
        maya_version = None
        for program in _maya_programs_for_repo(api, repo):
            candidate = linked.get(program.id)
            if candidate:
                maya_exe = candidate
                maya_version = program.version
                break

        if not maya_exe:
            QMessageBox.warning(
                None,
                "Maya Launcher",
                "No linked Maya executable found for this repo's required "
                "Maya version. Configure it in Settings > Software Linker.",
            )
            return True  # handled (with a warning) — do not fall back to OS default

        enabled_tool_ids = tools_store.enabled_tool_ids_for(
            api.local_config.active_project_id, api.local_config.active_repo_id
        )
        contributions = build_contributions(PLUGIN_DIR, api.app_root, enabled_tool_ids)
        env = _build_maya_env(os.environ.copy(), contributions, maya_version or "")

        repo_root = _repo_root_path(api, repo)
        mel_command = _set_project_and_open_command(repo_root, path)
        subprocess.Popen([maya_exe, "-command", mel_command], env=env)
        return True

    api.register_file_opener(ADDON_ID, MAYA_FILE_EXTENSIONS, open_maya_file)
    api.register_settings_tab(
        SettingsTabSpec(
            key=ADDON_ID,
            label="Maya Launcher",
            order=110,
            page_factory=lambda: MayaLauncherSettingsPage(api=api, tools_store=tools_store),
            on_activated=lambda page: page.refresh(),
            category=CATEGORY_REPO,
        )
    )
