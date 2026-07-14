# plugins/studio/maya_launcher/

Launches Maya with the linked executable (via Software Linker), auto-sets
the project to the repo root, and assembles Maya env vars from 7 nested
tools based on which are enabled for the active repo. Used to be 8 separate
`add-on/` folders (`MayaLauncher` plus 7 pure env-contributing add-ons that
did nothing but write into a shared `maya_launcher_env_bridge`
`PluginConfigStore`) — consolidated into one plugin since none of the 7
contributors ever registered anything besides that one bridge write; see
git history around 2026-07-14 if you need the old cross-add-on version.

## Files

- `manifest.json` — plugin id `maya_launcher`, entry point `plugin.py`.
- `plugin.py` — `register(api)`: registers the `.ma`/`.mb` file opener and
  the `Maya Launcher` settings tab. Also has the launch/merge logic:
  `_maya_programs_for_repo`, `_repo_root_path`, `_set_project_and_open_command`,
  `_build_maya_env` (see "Env merge" and "Auto set-project" below).
- `tools.py` — `TOOL_IDS`, `TOOL_FOLDERS`, `TOOL_LABELS`, and
  `build_contributions(plugin_dir, app_root, enabled_tool_ids)` — one
  private `_<tool>_contribution(tool_root, app_root) -> dict` function per
  nested tool, returning that tool's `{var_name: {"*": [...], "<version>": [...]}}`
  env contribution. This is the file to touch when adding an 8th nested
  tool or changing what an existing one contributes.
- `repo_tools_store.py` — `RepoToolsStore`: per-repo enable/disable state
  for the 7 tools (see "Per-repo tool toggle" below).
- `settings_page.py` — `MayaLauncherSettingsPage`: the Settings > Maya
  Launcher tab — per-tool checkboxes for the active repo, plus the Software
  Linker link-status readout (✅/⚠️ per required Maya `Program`).
- `AdvancedSkeleton/`, `MayaNgskin/`, `MayaToolkit/`, `mGear/`,
  `UkoreBrowser/`, `DreamwallPicker/`, `StudioLibrary/` — each tool's
  vendored payload (`maya-scripts/`, `maya-plug-ins/`, `maya-modules/`,
  `vendor/`, etc.), moved as-is from the old `add-on/<Name>/` folders with
  internal structure untouched — only each tool's own `manifest.json`/
  `plugin.py` were dropped, since they're no longer independently
  discovered/loaded. `tools.py`'s `TOOL_FOLDERS` maps each tool id to its
  folder name here (case-sensitive, kept as-is from the original add-ons).

## Per-repo tool toggle — owned entirely by this plugin

Unlike a repo-scoped `add-on/`, this plugin is always-on (loaded once at
app startup, not gated by `Repo.enabled_addon_ids`) — but its 7 nested
tools' env contributions ARE still gated per-repo, via `RepoToolsStore`
instead. Storage: `api.plugin_config_store("maya_launcher", shared=True)`
→ `data/plugins/studio/maya_launcher.json`, key shape
`{"repo_enabled_tools": {"<project_id>:<repo_id>": ["advanced_skeleton", ...]}}`.
**A repo with no entry defaults to all 7 enabled** — this matches the
pre-consolidation behavior (the old `maya_launcher_env_bridge` had no
per-repo filtering at all; every contributor's env vars were injected for
every repo, always — `Repo.enabled_addon_ids` was cosmetic for these 7
ids). Toggling happens in the `MayaLauncherSettingsPage` Settings tab, one
checkbox row per tool, scoped to whichever repo is currently active
(refreshed via `SettingsTabSpec.on_activated`, so switching repos then
reopening this tab shows the right state — see
`interface/settings/settings_view.py`). Every toggle self-persists
immediately (same convention every settings page in this app follows — no
Save/Cancel step).

This replaced the generic `Repo.enabled_addon_ids`/`RepoAddonPanelRegistry`
mechanism for these 7 ids specifically (a 2026-07-14 data migration moved
any repo's existing `enabled_addon_ids` entries for these ids into the new
store, then stripped them from `Repo.enabled_addon_ids`). The old
`register_repo_addon_panel` Repo-About sub-tab is gone too — the
link-status info it showed now lives in this same Settings tab instead of
a separate About sub-tab.

## Env merge (`tools.py` + `plugin.py::_build_maya_env`)

`build_contributions(plugin_dir, app_root, enabled_tool_ids)` returns
`{tool_id: {var_name: {"*": [path, ...], "<version>": [path, ...]}}}` for
exactly the tools `RepoToolsStore.enabled_tool_ids_for(...)` says are
enabled for the active repo. `"*"` = applies no matter which Maya version
launches (most contributions). An explicit version key (matching
`Program.version`, e.g. `"2024"`) applies only when that exact Maya version
launches — this is how MayaNgSkin keys its per-version `MAYA_PLUG_IN_PATH`
entries (`_maya_ngskin_contribution` globs `maya-plug-ins/`'s subfolders at
call time rather than hardcoding a version list, so adding/removing a
version folder on disk needs no code change).

| Tool | Contributes |
|---|---|
| `advanced_skeleton` | `PYTHONPATH` |
| `maya_ngskin` | `PYTHONPATH` + versioned `MAYA_PLUG_IN_PATH` |
| `maya_toolkit` | `PYTHONPATH` + flat `MAYA_PLUG_IN_PATH` |
| `mgear` | `MAYA_MODULE_PATH` + `MGEAR_SHIFTER_COMPONENT_PATH` |
| `ukore_browser` | `PYTHONPATH` (its own `maya-scripts/` **and** `api.app_root`, so `import core.store`/`core.paths` resolves inside Maya's Python — that's how its vendored `core/repo_context.py` talks to UkoreHub's own Project/Repo model) |
| `dreamwall_picker` | `PYTHONPATH` |
| `studio_library` | `PYTHONPATH` |

`mGear.mod` is itself version-aware (`+MAYAVERSION:2018 ...` blocks), so
`MAYA_MODULE_PATH` only needs mGear's flat `maya-modules` folder — Maya
resolves the right platform/version subfolder from the `.mod` file itself.
`ngSkinTools2.mll`, by contrast, is a compiled plug-in shipped **one build
per Maya version**, hence the versioned keying.

`plugin.py::_build_maya_env(base_env, contributions, maya_version)` is the
pure, independently-testable function that merges every contribution —
iterates `tool_id`s sorted for deterministic ordering; for each, each
`var_name`'s `"*"` paths then its `maya_version`-specific paths (if any)
are prepended in that order. **It prepends, it never replaces**:
```python
env[var_name] = f"{new_entry}{os.pathsep}{existing}" if existing else new_entry
```
This matters because an artist's machine may already have its own Maya/
mGear install contributing to `PYTHONPATH` etc. — replacing would silently
break whatever that install already relies on. Returns a **new** dict
rather than mutating the input, so callers can safely pass
`os.environ.copy()`.

## The SoftwareLinker dependency (shared-config convention, not an import)

`plugin.py` doesn't import `plugins/studio/software_linker/`'s code —
both agree on the literal string `"software_linker"` as a
`PluginConfigStore` id:
```python
SOFTWARE_LINKER_PLUGIN_ID = "software_linker"
linked = api.plugin_config_store(SOFTWARE_LINKER_PLUGIN_ID, shared=False)
maya_exe = linked.get(program.id)   # program.id is the Program catalog entry's id
```
`shared=False` because which local `maya.exe` path a specific artist's
machine has is inherently per-machine, not team data (contrast with
`RepoToolsStore`'s data above, which *is* shared). If SoftwareLinker's
plugin id or config key ever changes, this constant has to change in
lockstep — there's no compiler/test to catch drift, so grep both files if
you touch either. `_maya_programs_for_repo(api, repo)` is the shared lookup
used by both `open_maya_file` and `MayaLauncherSettingsPage`: walks
`repo.required_program_ids`, resolves each through `api.programs.get_program(id)`
(catching `core.exceptions.NotFoundError` for stale ids), keeps ones whose
`name` contains `"maya"` case-insensitively. If a repo requires multiple
Maya versions, `open_maya_file` picks the **first one with a linked path**
— it does not disambiguate further.

## Auto set-project on launch

`open_maya_file` sets Maya's project on launch so the artist never has to
do it by hand. Per studio convention, every repo's `workspace.mel` always
lives at the repo's own root — `_repo_root_path` computes
`Path(api.local_config.workspace_root) / repo.local_path` (`Repo.local_path`
is stored relative to the workspace root, same join `core/paths.py`'s
`resolve_repo_path` produces elsewhere, done directly here since
`open_maya_file` only has `repo`, not the owning `Project`). This goes
through Maya's `setProject` MEL command via the `-command` flag, **not**
the `-proj` CLI flag — `-proj` proved unreliable in practice (Maya's own
last-session project preference surfaced an unrelated "Path does not
exist" dialog even against a repo whose `workspace.mel` demonstrably sits
at repo root), whereas `setProject` is Maya's directly-documented,
always-available command. The scene is opened via `file -open -force`
inside the same MEL string (not a positional CLI arg) so `setProject` is
guaranteed to run first: `[maya_exe, "-command", mel_command]`, nothing
else on the command line.

## Failure mode: repo needs Maya but nothing is linked

`open_maya_file` deliberately does **not** silently fall back to the OS
file association when no linked `maya.exe` is found — it shows
`QMessageBox.warning(None, "Maya Launcher", ...)` telling the user to go to
Settings → Maya Launcher / Software Linker, and returns `True` (meaning
"handled", so the caller doesn't additionally fall back to
`open_with_default_app`). Silent fallback was explicitly rejected because
it would make missing env injection indistinguishable from a
working-but-unconfigured setup.

## Adding an 8th nested tool

1. Drop the tool's vendored payload folder here (e.g.
   `plugins/studio/maya_launcher/NewTool/`).
2. Add its id to `tools.py`'s `TOOL_FOLDERS`/`TOOL_LABELS`, and a
   `_new_tool_contribution(tool_root, app_root) -> dict` function following
   the existing 7 — check its actual folder layout before assuming a shape
   from the table above, don't guess.
3. Add it to `_CONTRIBUTION_BUILDERS`. That's it — `RepoToolsStore` and
   `MayaLauncherSettingsPage` both iterate `TOOL_IDS` generically, no
   further wiring needed.

## Extending this pattern to another DCC (Houdini, Nuke, Blender, ...)

A different, larger task than "add a nested tool" above — a new DCC needs
its own plugin, not a contribution to this one. Copy the shape, not the
Maya specifics: own `plugins/studio/<dcc>_launcher/` folder (own
`manifest.json`/`plugin.py`), its own `_xxx_programs_for_repo` lookup
(currently Maya-specific here by string-matching `"maya"` in
`program.name`, not extracted to a shared helper — do that extraction if a
second DCC launcher makes the duplication worth it),
`api.register_file_opener(id, [".ext1", ".ext2"], open_xxx_file)` (reuses
`FileOpenerRegistry` as-is), and its own `_build_xxx_env`
prepend-not-replace merge function if it has multiple nested tools, or none
at all if it's self-contained. Decide the SoftwareLinker config key
convention up front (same `program.id`-keyed dict shape this plugin uses)
so one SoftwareLinker settings page keeps working for every DCC launcher.
Note: `add-on/BlenderLauncher/` and `add-on/UnrealLauncher/` were removed
during this consolidation (2026-07-14) — neither had a real
`manifest.json`/`plugin.py`/`register(api)`, so there's no existing
Blender/Unreal launcher logic to build from; a Blender or Unreal launcher
plugin would be a from-scratch build following this pattern, not a
migration.

## Testing

`_build_maya_env`, `_maya_programs_for_repo`, and `tools.py`'s
`build_contributions`/`_<tool>_contribution` functions are pure/Qt-free and
worth covering if you touch them — but this plugin's `.py` files aren't
reachable by normal pytest `import` from outside their own package (the
loader always imports `plugin.py` standalone via
`importlib.util.spec_from_file_location`, same as any other plugin — see
`plugins/README.md`'s Testing section). Verify with a throwaway scratchpad
script that imports `plugins.studio.maya_launcher.tools`/`.repo_tools_store`
directly (both are real importable modules, just not part of a pytest
`tests/` package) and asserts on their pure-function outputs, or loads
`plugin.py` the same way the real loader does for anything that needs
`register(api)`'s closures specifically.
