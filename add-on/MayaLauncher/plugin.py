from __future__ import annotations

import os
import subprocess
from pathlib import Path

from PySide6.QtWidgets import QLabel, QMessageBox, QVBoxLayout, QWidget

from core.exceptions import NotFoundError

ADDON_ID = "maya_launcher"
# Convention-only string match with plugins/studio/software_linker/plugin.py
# — both resolve to the same data/plugins/local/software_linker.json via
# PluginConfigStore, no coupling API needed.
SOFTWARE_LINKER_PLUGIN_ID = "software_linker"

# Convention-only string match with every Maya env-contributing add-on
# (AdvancedSkeleton, MayaNgskin, MayaToolkit, mGear) — each writes its own
# `contributions[addon_id]` entry into this shared, studio-tracked
# PluginConfigStore at register() time. MayaLauncher is a pure bridge: it
# owns launching Maya with an assembled env, not the list of what goes
# into that env, so a new tool can start contributing paths without any
# change here. See the "contributions" shape below.
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"

MAYA_FILE_EXTENSIONS = [".ma", ".mb"]

# Wildcard key for a contribution that applies no matter which Maya version
# is launched (most tools). An explicit version key (e.g. "2024", matching
# Program.version) applies only when that exact Maya version is launched —
# needed for tools that ship a version-specific compiled plug-in, like
# MayaNgskin's per-version ngSkinTools2.mll.
ANY_VERSION = "*"


def _maya_programs_for_repo(api, repo):
    """Every Program the repo requires whose name contains "maya" —
    resolved via repo.required_program_ids, same lookup used by both the
    Repo Add-on panel and the file opener below."""
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
    workspace.mel always lives, per studio convention, so this is what
    gets passed to Maya's `setProject`. `repo.local_path` is stored
    relative to the workspace root (see core/store.py's `add_repo`), the
    same join every other page does (e.g. repo_about_page.py via
    core/paths.py's resolve_repo_path)."""
    return Path(api.local_config.workspace_root) / repo.local_path


def _mel_string(path: Path) -> str:
    """A filesystem path as a MEL string literal — forward slashes (MEL's
    own convention, sidesteps backslash-escaping ambiguity) with internal
    double-quotes escaped defensively."""
    return str(path).replace("\\", "/").replace('"', '\\"')


def _set_project_and_open_command(repo_root: Path, scene_path: Path) -> str:
    """Pure, testable: the MEL passed to Maya's `-command` flag. Uses the
    real `setProject` MEL command rather than the `-proj` CLI flag —
    `-proj`'s interactive-Maya support turned out unreliable in practice
    (a repo whose workspace.mel demonstrably sits at repo root still hit
    Maya's own "Path does not exist" project-restore dialog), whereas
    `setProject` is Maya's own always-available, directly-documented
    command for this. Opening the scene via `file -open -force` in the
    same command (instead of passing it as a positional CLI arg) guarantees
    setProject runs first."""
    return f'setProject "{_mel_string(repo_root)}"; file -open -force "{_mel_string(scene_path)}";'


def _build_maya_env(base_env: dict, contributions: dict, maya_version: str) -> dict:
    """Pure, testable: returns a new env dict with each contributing
    add-on's paths prepended (not replaced) onto the env var it targets —
    prepending keeps whatever the artist's own Maya/mGear install already
    put there. `contributions` is the bridge store's raw
    {addon_id: {var_name: {"*": [...], "<version>": [...]}}} shape;
    `maya_version` selects which version-specific entries also apply, on
    top of every "*" entry. Iterates addon_ids sorted for deterministic
    env var ordering across runs."""
    env = dict(base_env)
    for addon_id in sorted(contributions):
        for var_name, by_version in contributions[addon_id].items():
            paths = list(by_version.get(ANY_VERSION, [])) + list(by_version.get(maya_version, []))
            for new_entry in paths:
                existing = env.get(var_name)
                env[var_name] = f"{new_entry}{os.pathsep}{existing}" if existing else new_entry
    return env


def register(api) -> None:
    def panel_factory(repo) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        maya_programs = _maya_programs_for_repo(api, repo)
        if not maya_programs:
            label = QLabel("This repo doesn't require Maya.")
            label.setWordWrap(True)
            layout.addWidget(label)
            return widget

        linked = api.plugin_config_store(SOFTWARE_LINKER_PLUGIN_ID, shared=False)
        for program in maya_programs:
            path = linked.get(program.id)
            if path:
                text = f"✅ {program.name} v{program.version} — linked: {path}"
            else:
                text = (
                    f"⚠️ {program.name} v{program.version} — not linked. "
                    "Configure it in Settings > Software Linker."
                )
            label = QLabel(text)
            label.setWordWrap(True)
            layout.addWidget(label)
        return widget

    def open_maya_file(path: Path, repo) -> bool:
        # Only reachable when this repo has "maya_launcher" enabled as an
        # add-on AND the file was opened through UkoreHub (Repo Browser or
        # Recent Files) — never for Maya/files opened any other way.
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

        bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
        contributions = bridge.get("contributions", {})
        env = _build_maya_env(os.environ.copy(), contributions, maya_version or "")

        repo_root = _repo_root_path(api, repo)
        mel_command = _set_project_and_open_command(repo_root, path)
        subprocess.Popen([maya_exe, "-command", mel_command], env=env)
        return True

    api.register_repo_addon_panel(ADDON_ID, panel_factory)
    api.register_file_opener(ADDON_ID, MAYA_FILE_EXTENSIONS, open_maya_file)
