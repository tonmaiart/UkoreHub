from __future__ import annotations

from pathlib import Path

# Wildcard key for a contribution that applies no matter which Maya version
# is launched (most tools). An explicit version key (e.g. "2024", matching
# Program.version) applies only when that exact Maya version is launched —
# needed for tools that ship a version-specific compiled plug-in, like
# MayaNgskin's per-version ngSkinTools2.mll.
ANY_VERSION = "*"

# Every id here must match a subfolder of this plugin's own directory
# (case-sensitive) — each tool's vendored payload lives at
# plugins/studio/maya_launcher/<TOOL_FOLDERS[tool_id]>/.
TOOL_FOLDERS = {
    "advanced_skeleton": "AdvancedSkeleton",
    "maya_ngskin": "MayaNgskin",
    "maya_toolkit": "MayaToolkit",
    "mgear": "mGear",
    "ukore_browser": "UkoreBrowser",
    "dreamwall_picker": "DreamwallPicker",
    "studio_library": "StudioLibrary",
}

TOOL_LABELS = {
    "advanced_skeleton": "AdvancedSkeleton",
    "maya_ngskin": "MayaNgSkin",
    "maya_toolkit": "MayaToolkit",
    "mgear": "mGear",
    "ukore_browser": "Ukore Browser",
    "dreamwall_picker": "DreamwallPicker",
    "studio_library": "StudioLibrary",
}

TOOL_IDS = list(TOOL_FOLDERS)


def _advanced_skeleton_contribution(tool_root: Path, app_root: Path) -> dict:
    return {"PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts")]}}


def _maya_ngskin_contribution(tool_root: Path, app_root: Path) -> dict:
    # ngSkinTools2.mll is a compiled plug-in shipped once per Maya version
    # (maya-plug-ins/2018, .../2024, ...) — unlike the other tools here, a
    # single flat MAYA_PLUG_IN_PATH entry can't cover every version, so each
    # version subfolder becomes its own keyed contribution. Globs the folder
    # rather than hardcoding a version list, so adding/removing a version
    # subfolder on disk needs no code change.
    plug_in_root = tool_root / "maya-plug-ins"
    versioned_plug_in_paths: dict[str, list[str]] = {}
    if plug_in_root.is_dir():
        for version_dir in sorted(plug_in_root.iterdir()):
            if version_dir.is_dir():
                versioned_plug_in_paths[version_dir.name] = [str(version_dir)]
    return {
        "PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts")]},
        "MAYA_PLUG_IN_PATH": versioned_plug_in_paths,
    }


def _maya_toolkit_contribution(tool_root: Path, app_root: Path) -> dict:
    return {
        "PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts")]},
        "MAYA_PLUG_IN_PATH": {ANY_VERSION: [str(tool_root / "maya-plug-ins")]},
    }


def _mgear_contribution(tool_root: Path, app_root: Path) -> dict:
    # maya-modules/mGear.mod is a real Maya .mod file, itself version-aware
    # (+ MAYAVERSION:2018 ... / +MAYAVERSION:2019 ... per block) — Maya
    # resolves the right platform/version subfolder from the .mod file once
    # MAYA_MODULE_PATH points at its flat parent folder, so no per-version
    # keying is needed here (contrast with MayaNgskin).
    return {
        "MAYA_MODULE_PATH": {ANY_VERSION: [str(tool_root / "maya-modules")]},
        "MGEAR_SHIFTER_COMPONENT_PATH": {ANY_VERSION: [str(tool_root / "mgear-custom-component")]},
    }


def _ukore_browser_contribution(tool_root: Path, app_root: Path) -> dict:
    return {
        # app_root is contributed too so `import core.store` / `core.paths`
        # resolves inside Maya's Python — that's how core/repo_context.py
        # talks to UkoreHub's own Project/Repo model to find the active
        # repo root.
        "PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts"), str(app_root)]},
    }


def _dreamwall_picker_contribution(tool_root: Path, app_root: Path) -> dict:
    return {"PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts")]}}


def _studio_library_contribution(tool_root: Path, app_root: Path) -> dict:
    return {"PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts")]}}


_CONTRIBUTION_BUILDERS = {
    "advanced_skeleton": _advanced_skeleton_contribution,
    "maya_ngskin": _maya_ngskin_contribution,
    "maya_toolkit": _maya_toolkit_contribution,
    "mgear": _mgear_contribution,
    "ukore_browser": _ukore_browser_contribution,
    "dreamwall_picker": _dreamwall_picker_contribution,
    "studio_library": _studio_library_contribution,
}


def build_contributions(plugin_dir: Path, app_root: Path, enabled_tool_ids: list[str]) -> dict:
    """{tool_id: {var_name: {version_key: [paths]}}} for exactly the given
    (already-filtered-to-enabled) tool ids — same shape the old
    maya_launcher_env_bridge PluginConfigStore used to hold, just built
    in-process now instead of round-tripped through a shared JSON file,
    since every contributor lives inside this one plugin."""
    contributions = {}
    for tool_id in enabled_tool_ids:
        builder = _CONTRIBUTION_BUILDERS.get(tool_id)
        if builder is None:
            continue
        tool_root = plugin_dir / TOOL_FOLDERS[tool_id]
        contributions[tool_id] = builder(tool_root, app_root)
    return contributions
