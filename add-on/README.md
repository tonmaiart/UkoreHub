# add-on/

Repo-scoped, opt-in extensions — a **Repo** picks which discovered add-ons
apply to it via `Repo.enabled_addon_ids` (edited in Settings → Project Data
Editor). Contrast with `plugins/` (always-on, every project, no per-repo
toggle) — see `core/extensibility/README.md` for the full Plugins-vs-Add-ons
writeup if you haven't read it yet. This file is the "how do I write one"
guide; that one is the "how does discovery/loading work" reference.

Every immediate subfolder here (`add-on/<YourAddonName>/`) is discovered
independently — no nesting, no `studio/`/`local/` split like `plugins/` has
(everything under `add-on/` is git-tracked/shared, on purpose).

## Minimum folder shape

```
add-on/YourAddonName/
  manifest.json
  plugin.py
```

`manifest.json`:
```json
{
  "id": "your_addon",
  "name": "Your Addon",
  "version": "1.0.0",
  "api_version": 1,
  "entry_point": "plugin.py",
  "description": "One sentence — shown in Repo About, the repo editor's add-on picker, and Settings > Add-ons."
}
```
`id` must be globally unique across every plugin *and* add-on (both share
one discovery namespace) and is what you'll use everywhere else — as the
key in `Repo.enabled_addon_ids`, the argument to `api.register_*`, and the
`AddonMetadataStore` key (see below). `api_version` must match the app's
current `PLUGIN_API_VERSION` (`interface/plugin_api.py`) or your add-on is
skipped with a `PluginLoadFailure`, not a crash — check
`interface/settings_pages/addon_settings_page.py`'s "Failed to Load" list
if your add-on silently isn't showing up.

`plugin.py` needs exactly one function:
```python
def register(api) -> None:
    ...
```
Called once at app startup (`core/extensibility/loader.py`'s
`apply_plugins`), after every add-on has been discovered but with **no
guaranteed order** between add-ons — discovery sorts folders alphabetically
by name, so don't write a `register(api)` that assumes another specific
add-on has already run. If you need to depend on another add-on's output,
use the shared-`PluginConfigStore` convention below instead of trying to
call into its code directly (add-on `.py` files are loaded ad-hoc via
`importlib.util.spec_from_file_location`, not as real importable packages —
`import`ing another add-on's module doesn't work).

A broken `register(api)` (raises, or the module has no `register` at all)
is caught and recorded as a `PluginLoadFailure`, not a crash — see the
"Failed to Load" list in Settings → Add-ons/Plugins.

## `api` — what `register(api)` receives

`api` is a `PluginAPI` instance (`interface/plugin_api.py`), the exact same
object every plugin gets too. The two calls specific to repo-scoped add-on
behavior:

- `api.register_file_opener(addon_id, extensions, opener)` — claims
  responsibility for opening certain file extensions (e.g. launching an
  app with custom env vars) instead of the OS default association, when a
  file is opened through Repo Browser or Recent Files. `opener(path, repo)
  -> bool` returns whether it handled the file. **Only reachable when the
  active repo has `addon_id` in `Repo.enabled_addon_ids`** —
  `core/extensibility/file_opener.py`'s `FileOpenerRegistry` enforces this,
  so there's no risk of your opener firing for files opened outside
  UkoreHub or on a repo that hasn't enabled you.
- `api.register_repo_addon_panel(addon_id, panel_factory)` — a status
  widget (`panel_factory(repo) -> QWidget`) shown in Project Info → "Repo
  Add-on" whenever this add-on is enabled for the active repo. Purely
  informational (e.g. "is the linked executable configured?") — optional,
  skip it if your add-on has nothing to show.

The rest of the surface is shared with plugins, and just as usable from an
add-on:
- `api.programs` — the shared Program catalog (`ProgramStore`);
  `.get_program(id)` raises `core.exceptions.NotFoundError`, not
  `None`/`KeyError`.
- `api.metadata` — `MetadataStore` (the Project/Repo registry).
- `api.local_config` — per-machine `LocalConfigStore`.
- `api.git` — `GitService`.
- `api.app_root` — `Path` to the UkoreHub install root, for referencing
  your own add-on's files without guessing nesting depth from `__file__`
  (e.g. `api.app_root / "add-on" / "YourAddonName" / "some-subfolder"`).
- `api.plugin_config_store(plugin_id, *, shared: bool)` — namespaced JSON
  settings (see below).
- `api.register_git_hook`, `api.register_section`,
  `api.register_settings_tab`, `api.register_project_info_tab` — same
  registries plugins use; an add-on can register any of these too, though
  it's less common (most add-ons only need the two above).

## Sharing data with another add-on: `plugin_config_store`, not imports

`api.plugin_config_store(plugin_id, shared=True|False)` returns a
`PluginConfigStore` — free-form JSON, namespaced by `plugin_id`. Two
unrelated add-ons that independently construct a store with the **same
`plugin_id` string** share the same file — no coupling, no import, just
agreeing on a string and a JSON shape in advance. `shared=True` writes to
the git-tracked studio config dir (same data for every machine — use this
for anything that isn't machine-specific, like a folder path inside the
UkoreHub install); `shared=False` writes to the gitignored per-machine dir
(use this for things like a locally-linked executable path).

Two real, worked examples of this convention, both in
`add-on/MayaLauncher/plugin.py` — read that file plus the
`ukorehub-maya-launcher-addon` skill for the full write-up:
1. **Consumer reads another plugin's config**: MayaLauncher reads
   `plugins/studio/software_linker`'s per-machine `maya.exe` path via
   `api.plugin_config_store("software_linker", shared=False)`, without
   importing SoftwareLinker's code at all.
2. **Multiple add-ons feed one bridge, order-independent**: MayaLauncher
   itself doesn't hardcode Maya env vars — `add-on/AdvancedSkeleton`,
   `add-on/MayaNgskin`, `add-on/MayaToolkit`, and `add-on/mGear` each write
   their own env-path contribution into
   `api.plugin_config_store("maya_launcher_env_bridge", shared=True)` at
   `register()` time (each touching only its own key, never another
   add-on's), and MayaLauncher merges all of them when a `.ma`/`.mb` file
   is actually opened. This is the pattern to copy if you're writing an
   add-on that should feed data into another add-on without a fixed load
   order between them.

## Icon, description override, and required Program — not in code

`manifest.json`'s `name`/`description` are the fallback shown until an
admin edits an add-on's entry in **Settings → Add-ons**
(`interface/settings_pages/addon_settings_page.py`, backed by
`core/addon_store.py`'s `AddonMetadataStore` →
`data/addon_settings.json`, shared/git-tracked). That's also where an
add-on's **required Program(s)** are declared (e.g. "this add-on requires
Autodesk Maya") — deliberately *not* a manifest field or something
`register(api)` sets, so studio admins can retarget an add-on to a
different/renamed Program catalog entry without a code change. Declaring a
required program is what makes an add-on's card nest under that program's
`RequirementCard` in Repo About and the repo editor's add-on picker
(`core/addon_store.py`'s `group_addon_ids_by_program`) — an add-on with no
declared required program (yet) just shows in the "Other Add-ons" fallback
group, not hidden.

## Testing

`add-on/*.py` files aren't real importable packages (loaded via
`importlib.util.spec_from_file_location`, same as `plugins/`), so normal
`import` in a pytest test file can't reach them. If your `register(api)`
or any helper function is worth covering:
- Pure, Qt-free logic → extract it into a real `core/` module and test it
  normally (see `core/addon_store.py` + `tests/test_addon_store.py`).
- Logic that only makes sense inside `plugin.py` itself → verify with a
  throwaway scratchpad script that loads the module the same way the real
  loader does (`importlib.util.spec_from_file_location(...)` +
  `spec.loader.exec_module(module)`), then calls into it directly against
  a real `PluginConfigStore` backed by a temp file. See the
  `ukorehub-maya-launcher-addon` skill's "Testing" section for a concrete
  example of this pattern.
