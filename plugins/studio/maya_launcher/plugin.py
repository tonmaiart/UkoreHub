from __future__ import annotations

import os
import subprocess
from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from core.exceptions import NotFoundError
from interface.settings_tab_registry import CATEGORY_REPO, SettingsTabSpec
from plugins.studio.maya_launcher.repo_tools_store import RepoToolsStore
from plugins.studio.maya_launcher.settings_page import MayaLauncherSettingsPage

ADDON_ID = "maya_launcher"
# Convention-only string match with plugins/studio/software_linker/plugin.py
# — both resolve to the same data/plugins/local/software_linker.json via
# PluginConfigStore, no coupling API needed.
SOFTWARE_LINKER_PLUGIN_ID = "software_linker"
# Convention-only string match with every Maya env-contributing plugin
# (plugins/studio/AdvancedSkeleton, .../MayaNgskin, .../MayaToolkit,
# .../mGear, .../UkoreBrowser, .../DreamwallPicker, .../StudioLibrary,
# .../PublishApi, .../ModelPublisher, .../RigPublisher,
# .../AnimationPublisher) — each writes its own contributions[tool_id] entry
# (plus labels[tool_id]) into this shared, studio-tracked PluginConfigStore
# at register() time. This plugin is a pure bridge reader: it owns
# launching Maya with an assembled env, not the list of what goes into
# that env, so a new tool can start contributing paths with zero code
# change here — reverted 2026-07-19 to this pre-consolidation shape (see
# git history around 2026-07-14 for the version that briefly inlined every
# tool's env-building logic into this plugin instead of a shared bridge).
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"
# PublishApi is pure infrastructure — no artist-facing behavior or UI of
# its own, just path-resolution/versioning other tools (UkoreBrowser,
# ModelPublisher/RigPublisher/AnimationPublisher) import directly. Never
# gated by RepoToolsStore's per-repo toggle below (unlike every other tool,
# it isn't even offered as a checkbox in Settings), same reasoning
# plugins/studio/project_editor/'s "core": true manifest flag makes IT
# immune to the generic Enable-Plugin gating: there's no legitimate reason
# a repo would ever want it disabled, and doing so only breaks whatever
# else is enabled and imports it — `import PublishApi` failing inside
# Maya for a tool that's supposedly turned on.
PUBLISH_API_TOOL_ID = "publish_api"

MAYA_FILE_EXTENSIONS = [".ma", ".mb"]


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


_PLUGIN_FILE_EXTENSIONS = {".py", ".mll", ".pyd", ".so"}


def _force_load_plugin_names(contributions: dict, maya_version: str) -> list[str]:
    """Every compiled/script Maya plug-in file (.py/.mll/.pyd/.so) sitting
    directly in a contributed MAYA_PLUG_IN_PATH folder, by the module name
    Maya's own loadPlugin/pluginInfo commands identify it by (its filename
    without extension) — so open_maya_file can force-load them at launch
    instead of leaving the artist to tick "Auto Load" in Plug-in Manager by
    hand every session. Only sees plug-in files sitting directly in a
    contributed folder, same as Maya's own Plug-in Manager scan — a tool
    whose plug-in files live one level deeper (see MayaToolkit's nested
    maya-plug-ins/ subfolders) still won't be picked up here either."""
    names: list[str] = []
    seen: set[str] = set()
    for tool_id in sorted(contributions):
        by_version = contributions[tool_id].get("MAYA_PLUG_IN_PATH", {})
        paths = list(by_version.get(ANY_VERSION, [])) + list(by_version.get(maya_version, []))
        for path in paths:
            folder = Path(path)
            if not folder.is_dir():
                continue
            for entry in sorted(folder.iterdir()):
                if entry.is_file() and entry.suffix.lower() in _PLUGIN_FILE_EXTENSIONS and entry.stem not in seen:
                    seen.add(entry.stem)
                    names.append(entry.stem)
    return names


def _force_load_plugins_command(plugin_names: list[str]) -> str:
    """MEL that force-loads each plug-in by name, wrapped in `catch` so one
    plug-in failing to load (or already being marked loaded) can't abort
    the rest of the `-command` string — including the setProject/file-open
    that follows it. Runs before setProject/file-open so a scene that
    references plug-in node types (e.g. an ngSkinTools skin layer) opens
    without Maya flagging them as unknown nodes."""
    return "".join('catch(`loadPlugin -quiet "{}"`);'.format(name) for name in plugin_names)


def _build_maya_env(base_env: dict, contributions: dict, maya_version: str) -> dict:
    """Pure, testable: returns a new env dict with each enabled tool's paths
    prepended (not replaced) onto the env var it targets — prepending keeps
    whatever the artist's own Maya/mGear install already put there.
    `contributions` is the bridge's own already-filtered-to-enabled
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


def _read_bridge(api) -> tuple[dict, dict]:
    """Fresh read of the shared bridge's "contributions"/"labels" dicts —
    api.plugin_config_store() constructs a brand-new PluginConfigStore
    (loading from disk) on every call, so this always sees whatever every
    contributing tool plugin has written by now (see MAYA_ENV_BRIDGE_PLUGIN_ID
    above)."""
    bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
    return bridge.get("contributions", {}), bridge.get("labels", {})


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

        all_contributions, _labels = _read_bridge(api)
        enabled_tool_ids = set(
            tools_store.enabled_tool_ids_for(
                api.local_config.active_project_id, api.local_config.active_repo_id, list(all_contributions)
            )
        )
        contributions = {tid: c for tid, c in all_contributions.items() if tid in enabled_tool_ids}
        if PUBLISH_API_TOOL_ID in all_contributions:
            contributions[PUBLISH_API_TOOL_ID] = all_contributions[PUBLISH_API_TOOL_ID]
        env = _build_maya_env(os.environ.copy(), contributions, maya_version or "")

        repo_root = _repo_root_path(api, repo)
        plugin_names = _force_load_plugin_names(contributions, maya_version or "")
        mel_command = _force_load_plugins_command(plugin_names) + _set_project_and_open_command(repo_root, path)
        subprocess.Popen([maya_exe, "-command", mel_command], env=env)
        return True

    api.register_file_opener(ADDON_ID, MAYA_FILE_EXTENSIONS, open_maya_file, always_enabled=True)
    api.register_settings_tab(
        SettingsTabSpec(
            key=ADDON_ID,
            label="Maya Launcher",
            order=110,
            page_factory=lambda: MayaLauncherSettingsPage(
                api=api, tools_store=tools_store, read_bridge=lambda: _read_bridge(api)
            ),
            on_activated=lambda page: page.refresh(),
            category=CATEGORY_REPO,
        )
    )
