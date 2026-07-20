# plugins/studio/maya_launcher/

Launches Maya with the linked executable (via Software Linker), auto-sets
the project to the repo root, and assembles Maya env vars merged from
whatever independent Maya tool plugins have contributed to a shared
bridge. This plugin is a **pure bridge reader** — it owns launching Maya
with an assembled env, not the list of what goes into that env, so a new
tool can start contributing paths with zero code change here.

This is a **reverted architecture**, changed 2026-07-19. Between
2026-07-14 and 2026-07-19 this plugin briefly consolidated 8 separate
add-ons (itself plus 7 pure env-contributing add-ons that did nothing but
write into the same shared bridge) into one plugin with the 7 tools
nested inside its own folder (`tools.py`'s `TOOL_FOLDERS`/`build_contributions`)
— see git history around those dates if you need that version. It was
un-consolidated back to independent plugins because grouping unrelated
vendored tools under one plugin folder made "stay inside the folder the
task names" (see root `CLAUDE.md`) impossible to honor for a
single-tool change, and because a plugin catalog that lists "Maya
Launcher" as one opaque entry hides which individual tools a repo actually
depends on. The current shape is functionally identical to the
**original, pre-2026-07-14 add-on architecture** — see
`add-on/MayaLauncher/plugin.py` in git history for the version this was
restored from.

## Files

- `manifest.json` — plugin id `maya_launcher`, entry point `plugin.py`.
- `plugin.py` — `register(api)`: registers the `.ma`/`.mb` file opener and
  the `Maya Launcher` settings tab. Also has the launch/merge logic:
  `_maya_programs_for_repo`, `_repo_root_path`, `_set_project_and_open_command`,
  `_build_maya_env`, `_read_bridge` (see "Env merge" and "Auto set-project"
  below).
- `repo_tools_store.py` — `RepoToolsStore`: per-repo enable/disable state
  for whichever tool ids the bridge currently knows about (see "Per-repo
  tool toggle" below).
- `settings_page.py` — `MayaLauncherSettingsPage`: the Settings > Maya
  Launcher tab — per-tool checkboxes for the active repo (built once at
  construction from a `read_bridge()` snapshot — see below), plus the
  Software Linker link-status readout (✅/⚠️ per required Maya `Program`).

**The 7 nested tool payload folders that used to live here
(`AdvancedSkeleton/`, `MayaNgskin/`, `MayaToolkit/`, `mGear/`,
`UkoreBrowser/`, `DreamwallPicker/`, `StudioLibrary/`) all moved to their
own top-level `plugins/studio/<Name>/` folders on 2026-07-19.** Each is
its own plugin now (own `manifest.json` + `plugin.py`), contributing to
the shared bridge described below instead of being read directly off disk
by this plugin. See each one's own README for its specific vendored
payload shape.

**`UkorePublisher` went further still, the same day**: extracted out of
`MayaToolkit/maya-scripts/` into its own plugin, then immediately split
again into three type-specific plugins —
`plugins/studio/ModelPublisher/`, `plugins/studio/RigPublisher/`,
`plugins/studio/AnimationPublisher/` — each with its own dedicated UI
instead of one shared "pick a Type, then a Ticket" window. All three are
built on `plugins/studio/PublishApi/`, a new non-UI Maya-side library
(itself one of these bridge-contributing tool plugins) that resolves a
publish destination from the active repo's Project Editor pipeline
metadata and creates versioned publish folders — the single source of
truth those three, and eventually `UkoreBrowser`, share instead of each
carrying its own copy of that logic. See
`plugins/studio/PublishApi/README.md`.

## The `maya_launcher_env_bridge` shared bridge

`MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"` — a convention-only
string both this plugin and every contributing tool plugin agree on as a
`PluginConfigStore` id (`api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID,
shared=True)` → `data/plugins/studio/maya_launcher_env_bridge.json`), no
import between them at all. Each tool plugin's own `register(api)` writes
its entry unconditionally, every app start:

```json
{
  "contributions": {
    "<tool_id>": {"<VAR_NAME>": {"*": ["path", ...], "<maya_version>": ["path", ...]}}
  },
  "labels": {
    "<tool_id>": "Human-readable label for the Settings checkbox"
  }
}
```

`"*"` (`ANY_VERSION`) applies no matter which Maya version launches; an
explicit version key (matching `Program.version`, e.g. `"2024"`) applies
only when that exact Maya version launches — this is how MayaNgSkin keys
its per-version `MAYA_PLUG_IN_PATH` entries. This plugin's `_read_bridge(api)`
does a **fresh** read (a new `PluginConfigStore` is constructed and loaded
from disk on every call) — safe regardless of plugin load order, since
`open_maya_file`/the Settings tab are only ever triggered by the user well
after every plugin has finished registering (see `core/extensibility/loader.py`).

| Tool plugin | Contributes |
|---|---|
| `plugins/studio/AdvancedSkeleton` | `PYTHONPATH` |
| `plugins/studio/MayaNgskin` | `PYTHONPATH` + versioned `MAYA_PLUG_IN_PATH` |
| `plugins/studio/MayaToolkit` | `PYTHONPATH` + flat `MAYA_PLUG_IN_PATH` |
| `plugins/studio/mGear` | `MAYA_MODULE_PATH` + `MGEAR_SHIFTER_COMPONENT_PATH` |
| `plugins/studio/UkoreBrowser` | `PYTHONPATH` (its own `maya-scripts/` **and** `api.app_root`, so `import core.store`/`core.paths` resolves inside Maya's Python — that's how its vendored `core/repo_context.py` talks to UkoreHub's own Project/Repo model) |
| `plugins/studio/DreamwallPicker` | `PYTHONPATH` |
| `plugins/studio/StudioLibrary` | `PYTHONPATH` |
| `plugins/studio/PublishApi` | `PYTHONPATH` (its own `maya-scripts/` **and** `api.app_root`, same reason as `UkoreBrowser` above) |
| `plugins/studio/ModelPublisher` | `PYTHONPATH` |
| `plugins/studio/RigPublisher` | `PYTHONPATH` |
| `plugins/studio/AnimationPublisher` | `PYTHONPATH` |
| `plugins/studio/UkorePlayblast` | `PYTHONPATH` |

`mGear.mod` is itself version-aware (`+MAYAVERSION:2018 ...` blocks), so
`MAYA_MODULE_PATH` only needs mGear's flat `maya-modules` folder — Maya
resolves the right platform/version subfolder from the `.mod` file itself.
`ngSkinTools2.mll`, by contrast, is a compiled plug-in shipped **one build
per Maya version**, hence the versioned keying.

## Per-repo tool toggle — owned entirely by this plugin

Unlike the tool plugins above (each always registered, unconditionally
writing its bridge entry), whether a tool's env contribution actually
applies to a given repo's Maya launch is gated per-repo by
`RepoToolsStore` instead. Storage: `api.plugin_config_store("maya_launcher",
shared=True)` → `data/plugins/studio/maya_launcher.json`, key shape
`{"repo_disabled_tools": {"<project_id>:<repo_id>": ["advanced_skeleton", ...]}}`
— **an opt-OUT list** (the tools turned off for this repo), not opt-in.
**A repo with no entry, or an empty list, has every currently-known tool id
enabled** (`RepoToolsStore.enabled_tool_ids_for` takes `all_tool_ids` — read
live off the bridge by `plugin.py`, not a hardcoded list — and returns it
minus whatever's in the disabled set). Toggling happens in the
`MayaLauncherSettingsPage` Settings tab, one checkbox row per tool, scoped
to whichever repo is currently active (refreshed via
`SettingsTabSpec.on_activated`, so switching repos then reopening this tab
shows the right state — see `interface/settings/settings_view.py`). Every
toggle self-persists immediately (same convention every settings page in
this app follows — no Save/Cancel step).

**Why opt-out, not opt-in:** changed 2026-07-19 after two real
`ModuleNotFoundError`s (`PublishApi`, then `RigPublisher`) on repos whose
tool list had been customized *before* those plugins existed. The
original design stored the enabled set directly — so a repo with an
explicit customized list had no way to tell "this tool was explicitly
unchecked" apart from "this tool didn't exist yet when the list was last
saved," and silently excluded every tool added afterward until someone
noticed and re-checked it by hand in Settings. Storing the disabled set
instead fixes this permanently: a brand-new tool id is never in *any*
repo's disabled set until someone actually unchecks it, so it defaults to
enabled everywhere — the same "no entry = everything on" behavior this
store has always had for repos with zero customization, now also true for
tool ids added after a repo was first customized.

`RepoToolsStore._migrate_legacy_entry` handles the one-time conversion:
the old `repo_enabled_tools` opt-in shape is read (never written again)
and converted to `repo_disabled_tools` as `_LEGACY_TOOL_IDS - old_enabled_set`
— `_LEGACY_TOOL_IDS` is the fixed set of exactly the 7 tool ids the
pre-2026-07-19 Settings UI could ever have offered a checkbox for, so this
correctly recovers "what did this repo actually opt out of" without
guessing, and never needs a new entry added to it (a second migration like
this, if ever needed again, would use a snapshot of whatever
`_LEGACY_TOOL_IDS` — or its 2026-07-19 successor — looked like at *that*
point instead).

**`plugins/studio/PublishApi` is never gated by this at all**, on top of
the above — it's pure infrastructure (no artist-facing behavior or UI of
its own, only path-resolution/versioning functions other tools import
directly: `UkoreBrowser`, `ModelPublisher`/`RigPublisher`/
`AnimationPublisher`), so there's no legitimate reason to ever disable it
per-repo, opt-out storage or not. `open_maya_file` force-includes its
contribution regardless of `RepoToolsStore`'s per-repo list
(`PUBLISH_API_TOOL_ID` in `plugin.py`), and `MayaLauncherSettingsPage`
excludes it from the checkbox list entirely (`_PUBLISH_API_TOOL_ID` in
`settings_page.py`) rather than showing a toggle that would silently do
nothing.

This toggle mechanism is a maya_launcher-owned enhancement layered on top
of the bridge — it existed before the 2026-07-14 consolidation too, and
was deliberately kept when un-consolidating back to independent plugins on
2026-07-19 (the 2026-07-14 README previously noted this store "replaced
the generic `Repo.enabled_addon_ids`/`RepoAddonPanelRegistry` mechanism
for these 7 ids" — that migration is still in effect; toggling stayed on
`RepoToolsStore`, it did not revert to `Repo.enabled_addon_ids`).

## Env merge (`plugin.py::_build_maya_env`)

`open_maya_file` reads the bridge's full `"contributions"` dict, filters
it down to `RepoToolsStore.enabled_tool_ids_for(...)` for the active repo,
then `_build_maya_env(base_env, contributions, maya_version)` merges every
remaining contribution — iterates `tool_id`s sorted for deterministic
ordering; for each, each `var_name`'s `"*"` paths then its
`maya_version`-specific paths (if any) are prepended in that order. **It
prepends, it never replaces**:
```python
env[var_name] = f"{new_entry}{os.pathsep}{existing}" if existing else new_entry
```
This matters because an artist's machine may already have its own Maya/
mGear install contributing to `PYTHONPATH` etc. — replacing would silently
break whatever that install already relies on. Returns a **new** dict
rather than mutating the input, so callers can safely pass
`os.environ.copy()`.

## Force-loading compiled/script plug-ins on launch

Being on `MAYA_PLUG_IN_PATH` only makes a plug-in *visible* in Maya's
Plug-in Manager — it doesn't load it. Before this, an artist had to tick
"Auto Load" by hand, per plug-in, per machine, every time. `open_maya_file`
now force-loads them instead: `_force_load_plugin_names(contributions,
maya_version)` scans every contributed `MAYA_PLUG_IN_PATH` folder for
`.py`/`.mll`/`.pyd`/`.so` files sitting **directly** in it (same shallow
scan Maya's own Plug-in Manager does — a file nested one level deeper,
like most of `MayaToolkit`'s `maya-plug-ins/` subfolders, still won't be
found), and `_force_load_plugins_command` turns that into
`catch(\`loadPlugin -quiet "name"\`);` MEL for each, prepended onto the
`-command` string **before** `setProject`/`file -open` — so a scene
referencing plug-in node types (an ngSkinTools skin layer, say) opens
without Maya flagging them as unknown nodes. Each load is wrapped in
`catch` so one plug-in failing (or already being loaded) can't take the
rest of the `-command` string down with it.

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

## Adding a new nested tool

1. Create a new `plugins/studio/<Name>/` plugin folder (own `manifest.json`
   + `plugin.py`), following the shape any of the existing tool plugins
   above use — `register(api)` reads/updates the bridge's `"contributions"`
   and `"labels"` dicts and writes them back, nothing else.
2. That's it — this plugin never needs a code change: `_read_bridge`,
   `RepoToolsStore`, and `MayaLauncherSettingsPage` all iterate whatever
   the bridge currently knows about generically.

## Extending this pattern to another DCC (Houdini, Nuke, Blender, ...)

A different, larger task than "add a nested tool" above — a new DCC needs
its own launcher plugin, not a contribution to this one. Copy the shape,
not the Maya specifics: own `plugins/studio/<dcc>_launcher/` folder (own
`manifest.json`/`plugin.py`), its own `_xxx_programs_for_repo` lookup
(currently Maya-specific here by string-matching `"maya"` in
`program.name`, not extracted to a shared helper — do that extraction if a
second DCC launcher makes the duplication worth it),
`api.register_file_opener(id, [".ext1", ".ext2"], open_xxx_file)` (reuses
`FileOpenerRegistry` as-is), and its own `_build_xxx_env`
prepend-not-replace merge function if it has multiple nested tools, or none
at all if it's self-contained. Decide its own shared-bridge `PluginConfigStore`
id convention up front (same `{tool_id: {var_name: {...}}}` shape this
plugin uses) so a new DCC's contributing tool plugins have something to
write into. Note: `add-on/BlenderLauncher/` and `add-on/UnrealLauncher/`
were removed during the 2026-07-14 consolidation — neither had a real
`manifest.json`/`plugin.py`/`register(api)`, so there's no existing
Blender/Unreal launcher logic to build from; a Blender or Unreal launcher
plugin would be a from-scratch build following this pattern, not a
migration.

## Testing

`_build_maya_env`, `_maya_programs_for_repo` are pure/Qt-free and worth
covering if you touch them — but this plugin's `.py` files aren't
reachable by normal pytest `import` from outside their own package (the
loader always imports `plugin.py` standalone via
`importlib.util.spec_from_file_location`, same as any other plugin — see
`plugins/README.md`'s Testing section). Verify with a throwaway scratchpad
script that imports `plugins.studio.maya_launcher.repo_tools_store`
directly (a real importable module, just not part of a pytest `tests/`
package) and asserts on its pure-function outputs, or loads `plugin.py`
the same way the real loader does for anything that needs `register(api)`'s
closures specifically.
