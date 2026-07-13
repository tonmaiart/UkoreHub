---
name: ukorehub-maya-launcher-addon
description: Reference for UkoreHub's MayaLauncher add-on (add-on/MayaLauncher/plugin.py), the Maya env bridge it hosts (contributed to by add-on/AdvancedSkeleton, add-on/MayaNgskin, add-on/MayaToolkit, add-on/mGear), and the SoftwareLinker plugin dependency (C:\Tonmai\UkoreHub). Use this whenever modifying MayaLauncher, SoftwareLinker, or any Maya env-contributing add-on; adding another DCC-launching add-on (Houdini, Nuke, Blender, etc.) modeled on the same pattern; or debugging why a Maya environment variable isn't set when a .ma/.mb file is opened through UkoreHub. Trigger on mentions of Maya env vars, MAYA_PLUG_IN_PATH, MAYA_MODULE_PATH, MGEAR_SHIFTER_COMPONENT_PATH, mGear, ngSkinTools, AdvancedSkeleton, or "DCC launcher" even if the user doesn't name the add-on directly.
---

# MayaLauncher add-on — architecture reference

MayaLauncher is UkoreHub's first (and so far only) **add-on** — see the
`ukorehub-core` skill for the Plugins-vs-Add-ons distinction if that's not
already clear; this skill assumes it. It lives at
`add-on/MayaLauncher/plugin.py` and registers two independent capabilities
in `register(api)`:

```python
api.register_repo_addon_panel(ADDON_ID, panel_factory)
api.register_file_opener(ADDON_ID, MAYA_FILE_EXTENSIONS, open_maya_file)
```

Keep these mentally separate — they're triggered completely differently:

1. **`panel_factory`** — a status widget shown in the repo's "Repo Add-on"
   tab (Project Info → Repo Add-on) whenever this add-on is enabled for
   that repo. Purely informational: shows which of the repo's required Maya
   `Program`s are linked to a real executable, via ✅/⚠️ labels.
2. **`open_maya_file`** — the actual env-injection logic. Only reachable
   through `core.extensibility.file_opener.FileOpenerRegistry`, and only
   when **both** conditions hold: the file being opened has a `.ma`/`.mb`
   extension, **and** the active repo has `"maya_launcher"` in
   `Repo.enabled_addon_ids`. See the `ukorehub-interface` skill's "File-open
   flow" section for how a double-click in Repo Browser (or a Recent Files
   click) actually reaches this function. **This is the mechanism that
   guarantees env injection never happens when Maya is opened directly,
   outside UkoreHub** — there's no OS-level or Maya-level hook, it's purely
   "did the click go through `FileOpenerRegistry.find_opener`."

## The SoftwareLinker dependency (shared-config convention, not an import)

MayaLauncher doesn't import SoftwareLinker's code. Instead both agree on
the literal string `"software_linker"` as a `PluginConfigStore` id:

```python
SOFTWARE_LINKER_PLUGIN_ID = "software_linker"
...
linked = api.plugin_config_store(SOFTWARE_LINKER_PLUGIN_ID, shared=False)
maya_exe = linked.get(program.id)   # program.id is the Program catalog entry's id
```

This is the general pattern for cross-plugin data sharing in UkoreHub — see
`ukorehub-core` skill's `config_store.py` entry. `shared=False` because
which local `maya.exe` path a specific artist's machine has is inherently
per-machine, not team data (contrast with `Repo.enabled_addon_ids`, which
*is* shared). If SoftwareLinker's plugin id or config key ever changes, this
constant has to change in lockstep — there is no compiler/test to catch a
drift between them, so grep both files if you touch either.

`_maya_programs_for_repo(api, repo)` is the shared lookup used by both
`panel_factory` and `open_maya_file`: walks `repo.required_program_ids`,
resolves each through `api.programs.get_program(id)` (catching
`core.exceptions.NotFoundError` for stale ids), and keeps ones whose `name`
contains `"maya"` case-insensitively. If a repo requires multiple Maya
versions, `open_maya_file` picks the **first one with a linked path** — it
does not disambiguate further.

## MayaLauncher is a bridge, not the owner of what goes into the env

MayaLauncher used to hardcode all four Maya env vars to one shared
`plugins/MayaToolkit/` tree. That's gone — MayaLauncher now owns *launching*
Maya with an assembled env, but not the list of what goes into that env.
Four separate add-ons each own their own real content and register their
own contribution:

| Add-on | Folder | Contributes |
|---|---|---|
| `add-on/AdvancedSkeleton` | `maya-scripts/` | `PYTHONPATH` |
| `add-on/MayaNgskin` | `maya-scripts/` + per-version `maya-plug-ins/<version>/` | `PYTHONPATH` + versioned `MAYA_PLUG_IN_PATH` |
| `add-on/MayaToolkit` | `maya-scripts/` + `maya-plug-ins/` (both flat) | `PYTHONPATH` + `MAYA_PLUG_IN_PATH` |
| `add-on/mGear` | `maya-modules/` (has a real `.mod` file) + `mgear-custom-component/` | `MAYA_MODULE_PATH` + `MGEAR_SHIFTER_COMPONENT_PATH` |

`mGear.mod` is itself version-aware (`+ MAYAVERSION:2018 ...` blocks), so
`MAYA_MODULE_PATH` only needs mGear's flat `maya-modules` folder — Maya
resolves the right platform/version subfolder from the `.mod` file itself.
`ngSkinTools2.mll`, by contrast, is a compiled plug-in shipped **one build
per Maya version** (`maya-plug-ins/2018/`, `.../2024/`, ...), so MayaNgskin
can't contribute a single flat `MAYA_PLUG_IN_PATH` entry — it keys its
contribution by version instead (see below). Check folder contents
directly before assuming either shape for a new tool; don't guess from this
table alone if the tool's own layout looks different.

### The bridge contract (`maya_launcher_env_bridge`)

No core/PluginAPI changes were needed — this reuses the exact same
"agree on a shared string ID, talk through `PluginConfigStore`" convention
as the SoftwareLinker dependency below. Every contributing add-on's
`register(api)` writes into:

```python
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
contributions = bridge.get("contributions", {})
contributions[ADDON_ID] = {
    "PYTHONPATH": {"*": [str(addon_root / "maya-scripts")]},
}
bridge.set("contributions", contributions)
```

Shape: `{addon_id: {var_name: {"*": [path, ...], "<version>": [path, ...]}}}`.
`"*"` = applies no matter which Maya version launches (most contributions).
An explicit version key (matching `Program.version`, e.g. `"2024"`) =
applies only when that exact Maya version launches — this is how
MayaNgskin keys its per-version `MAYA_PLUG_IN_PATH` entries (it globs
`maya-plug-ins/`'s subfolders at register time rather than hardcoding a
version list, so adding/removing a version folder on disk needs no code
change). `shared=True` because these are static folder paths under the
UkoreHub install itself — same for every machine — unlike SoftwareLinker's
per-machine `maya.exe` path below.

Each add-on overwrites only its own `addon_id` key on every app start
(self-healing if its folder moves), never another add-on's entry — so
there is **no load-order dependency** between contributors and
MayaLauncher. This matters concretely: `add-on/` discovery is alphabetical
by folder name, so `AdvancedSkeleton` registers *before* `MayaLauncher`
does. If the bridge were a live API call instead of a config-store
mailbox, that ordering would break on day one.

MayaLauncher itself reads the whole bridge only when a file is actually
opened (`open_maya_file`, long after every add-on has registered):
```python
bridge = api.plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID, shared=True)
contributions = bridge.get("contributions", {})
env = _build_maya_env(os.environ.copy(), contributions, maya_version)
```
`_build_maya_env(base_env: dict, contributions: dict, maya_version: str) -> dict`
is the pure, independently-testable function that merges every
contribution — deliberately factored out of `open_maya_file` so its logic
can be exercised without spinning up `subprocess.Popen` or a
`QMessageBox`. Iterates `addon_id`s sorted for deterministic ordering; for
each, each `var_name`'s `"*"` paths then its `maya_version`-specific paths
(if any) are prepended in that order. **It prepends, it never replaces**:
```python
env[var_name] = f"{new_entry}{os.pathsep}{existing}" if existing else new_entry
```
This matters because an artist's machine may already have its own Maya/
mGear install contributing to `PYTHONPATH` etc. — replacing would silently
break whatever that install already relies on. It also returns a **new**
dict (`dict(base_env)`) rather than mutating the input, so callers can
safely pass `os.environ.copy()` without worrying about side effects on the
copy they hand in.

## Auto set-project on launch

`open_maya_file` sets Maya's project on launch, so the artist never has to
do it by hand. Per studio convention, every repo's `workspace.mel` always
lives at the repo's own root. `repo_root` comes from
`_repo_root_path(api, repo) -> Path(api.local_config.workspace_root) /
repo.local_path` — `Repo.local_path` is stored **relative to the workspace
root** (see `core/store.py`'s `add_repo`), the same join
`core/paths.py`'s `resolve_repo_path` produces elsewhere in the app, just
done directly here since `open_maya_file` only has `repo`, not the owning
`Project` (needed for `resolve_repo_path`'s `project_name` argument).

This goes through Maya's `setProject` MEL command via the `-command` flag,
**not** the `-proj` CLI flag: `-proj` was tried first and turned out
unreliable in practice — even against a repo whose `workspace.mel`
demonstrably sits at repo root, Maya still surfaced its own unrelated
"Path does not exist" project-restore dialog on launch (apparently from
Maya's own last-session project preference, not something `-proj`
overrides cleanly). `setProject` is Maya's directly-documented,
always-available MEL command for this, so it's the reliable choice.
`_set_project_and_open_command(repo_root, scene_path) -> str` is the pure,
testable function building the MEL string:
```python
f'setProject "{_mel_string(repo_root)}"; file -open -force "{_mel_string(scene_path)}";'
```
`_mel_string` converts a `Path` to a MEL string literal (forward slashes,
escaped double-quotes). The scene file is opened via `file -open -force`
inside this same MEL string — **not** passed as a positional CLI
argument — specifically so `setProject` is guaranteed to run first; the
final `subprocess.Popen` call is `[maya_exe, "-command", mel_command]`,
nothing else.

## Failure mode: repo needs Maya but nothing is linked

`open_maya_file` deliberately does **not** silently fall back to the OS
file association when no linked `maya.exe` is found for the repo's
required Maya `Program`(s) — it shows
`QMessageBox.warning(None, "Maya Launcher", ...)` telling the user to go to
Settings → Software Linker, and returns `True` (meaning "handled" to
`FileOpenerRegistry`'s caller, so `RepoBrowserPage._open_file` does *not*
additionally fall back to `open_with_default_app`). If you're debugging "the
file just doesn't open," check whether this warning fired — silent fallback
was explicitly rejected because it would make missing env injection
indistinguishable from a working-but-unconfigured setup.

## Adding a fifth Maya env contributor

No MayaLauncher change needed — new folder under `add-on/`, own
`manifest.json` + a `plugin.py` whose `register(api)` writes its own
`contributions[ADDON_ID]` entry into the bridge (see the contract above).
No `register_file_opener`/`register_repo_addon_panel` call needed either —
MayaLauncher stays the sole `.ma`/`.mb` opener and status panel; a
contributor is just a silent env-path source. After it ships, set its
required Program (e.g. "Autodesk Maya") via the Add-on Settings page
(`interface/settings_pages/addon_settings_page.py`, backed by
`core/addon_store.py`'s `AddonMetadataStore`) — that's what makes it group
under the Maya requirement card in Repo About / the repo editor's add-on
picker, not anything hardcoded in the add-on itself.

## Extending this pattern to another DCC (Houdini, Nuke, Blender, ...)

This is a different, larger pattern than "add a Maya env contributor"
above — a new DCC needs its own launcher add-on, not just a bridge
contribution to MayaLauncher's. Copy the shape, not the Maya specifics:
1. New add-on folder under `add-on/`, own `manifest.json` + `plugin.py`.
2. A `_xxx_programs_for_repo` lookup mirroring `_maya_programs_for_repo`
   (or generalize it — it's currently Maya-specific by string-matching
   `"maya"` in `program.name`, not extracted to a shared helper).
3. Its own bridge convention if more than one add-on will need to
   contribute env paths to it (mirror `maya_launcher_env_bridge`'s shape),
   or a single pure `_build_xxx_env` function if it's self-contained —
   either way, prepend-not-replace, independently testable without Qt or
   subprocess.
4. `api.register_file_opener(ADDON_ID, [".ext1", ".ext2"], open_xxx_file)`
   — reuses `FileOpenerRegistry` as-is, no core changes needed.
5. Decide the SoftwareLinker config key convention up front (same
   `program.id`-keyed dict shape MayaLauncher uses) so a single
   SoftwareLinker settings page keeps working for every DCC add-on without
   changes.

## Testing

`_build_maya_env` and `_maya_programs_for_repo` have no pytest coverage —
per the `ukorehub-core` skill's testing-conventions note, files under
`add-on/` are loaded ad-hoc via `importlib.util.spec_from_file_location`
and aren't real importable packages, so normal pytest `import` doesn't
reach them. They (and every contributing add-on's `register(api)`) were
verified with a throwaway scratchpad script that loads each module the
same way the real loader does:
```python
spec = importlib.util.spec_from_file_location("maya_launcher_plugin", "add-on/MayaLauncher/plugin.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```
then, for the contributors, calls `module.register(fake_api)` against a
real `PluginConfigStore` backed by a temp file and inspects the resulting
`contributions` dict; for MayaLauncher, calls `module._build_maya_env(...)`
directly with assertions on prepend behavior, non-mutation of the input
dict, and that a version with no matching MayaNgskin plug-in build is
omitted rather than erroring. If you add real pytest coverage for an
add-on later, this loader snippet is the way in — consider whether it's
worth promoting to a shared test helper if a new add-on needs the same
treatment. `core/addon_store.py`'s `AddonMetadataStore` and
`group_addon_ids_by_program`, by contrast, are plain Qt-free `core/` code
and do have real pytest coverage (`tests/test_addon_store.py`).

`tests/test_file_opener_registry.py` covers the registry mechanics
generically (match by addon+extension, gating by enabled_addon_ids,
case-insensitive extensions, first-match-wins, duplicate registration
allowed) — that suite doesn't know about Maya specifically and doesn't need
updating when MayaLauncher's own logic changes, only when
`FileOpenerRegistry` itself changes.
