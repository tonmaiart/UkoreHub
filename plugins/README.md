# plugins/

UkoreHub's own sub-systems. See `core/extensibility/README.md` for the
discovery/loading mechanism if you haven't read it yet — this file is the
"how do I write one" guide; that one is the "how does discovery/loading
work" reference.

Three roots, all scanned by the same `discover_plugins()` (see
`launcher.py`) — they differ along two independent axes: whether the
plugin ships bundled with the app vs. is fetched separately, and whether
it's on by default per repo vs. opt-in:
- `core/` — git-tracked, ships bundled with the app (distributed via
  `self_update.py`'s whole-tree `git pull`, same as `data/programs.json`),
  **always on** for every repo — no per-repo opt-out at all (2026-08-04:
  there used to be an opt-out via Settings > Repo > Enable Plugin,
  `Repo.active_plugin_ids`, still checked by default; removed once every
  `plugins/core/` plugin was made unconditionally visible, matching the
  handful that were already flagged load-bearing). Explorer, Submit, and
  Software Linker all live here — reserve this root for functionality
  every repo genuinely needs; anything repo-specific belongs in
  `repo_internal/` instead. See `core/extensibility/README.md`.
- `repo_internal/` — also git-tracked and bundled with the app, but
  **opt-in**: hidden for a repo until that repo explicitly requires it
  (`Repo.required_plugin_ids`, same page as above), the same "off until
  required" shape as a Program requirement. Use this for a bundled plugin
  that only some repos actually need — unlike `core/`, adding one here
  doesn't turn it on for every existing repo.
- `cache/plugins/` (outside this folder, at the repo root, gitignored) —
  **repo plugins**: each one is its own separate git clone (its own
  remote/history, not part of this repo at all), fetched/updated on demand
  only for a repo that requires it. Not bundled with the app in any sense —
  see `plugin_source()` returning `"repo"` for one of these
  (`core/extensibility/loader.py`). `AdvancedSkeleton`, `DreamwallPicker`,
  `mGear`, `StudioLibrary`, `UkoreShot`, and `MayaNgSkin` are the first
  plugins converted to this shape; a `plugin.py` here locates its own folder via
  `Path(__file__).resolve().parent` rather than `api.app_root`, since it
  isn't at a fixed path relative to the app install. Note there's no
  auto-fetch/clone mechanism implemented anywhere yet — `launcher.py` only
  `mkdir`s `cache/plugins/` and discovers whatever's already physically
  cloned there; every plugin in this root today was cloned into place by
  hand. `UkoreShot` (a genuine multi-file plugin, unlike the single-file
  `mGear`/`StudioLibrary`) is the reference example for how a multi-file
  repo plugin wires up its own sibling imports without a `plugins.*`
  dotted path — see its own `plugin.py` and top-level `README.md`.

There is no more `plugins/local/` — the old gitignored/per-machine
prototyping root was removed 2026-08-04 (unused). Prototype a new plugin
directly under `core/` or `repo_internal/` instead.

## Working on a single plugin — stay inside its folder

When a task names a specific plugin (or the target path is under
`plugins/core/<Name>/`, `plugins/repo_internal/<Name>/`, or
`cache/plugins/<Name>/`), read and edit **only that folder**. Don't open a
sibling plugin "just in case" — each one is
independent, and reading one has zero information value for working on a
different one. Check the plugin's own `README.md` first if it has one
(same folder-README convention as `core/`/`interface/` — see root
`CLAUDE.md`).

If a task genuinely needs data from another plugin, that's almost always
the shared-`plugin_config_store` convention below (a `plugin_id` string + a
documented JSON shape), not a reason to read the other plugin's source. The
one real exception is explicit cross-plugin debugging — say so and read
both deliberately, rather than defaulting to broad exploration for a
single-plugin task. See the `ukorehub-plugin` skill for the fuller writeup.

## Minimum folder shape

```
plugins/core/YourPluginName/
  manifest.json
  plugin.py
```

`manifest.json`:
```json
{
  "id": "your_plugin",
  "name": "Your Plugin",
  "version": "0.1.0",
  "api_version": 1,
  "entry_point": "plugin.py",
  "description": "One sentence describing what this plugin registers.",
  "requires": ["other_plugin_id"]
}
```
`id` must be globally unique across every plugin. `api_version` must match
the app's current `PLUGIN_API_VERSION` (`interface/plugin_api.py`) or your
plugin is skipped with a `PluginLoadFailure`, not a crash.

`requires` (optional, defaults to `[]`) lists the plugin `id`s this plugin
can't function without — for a `repo_internal`/`cache/plugins` plugin that
depends on another opt-in plugin also being enabled for the repo, not for
declaring a load-order dependency (there is none — see above). It's only
enforced at the UI layer, in Settings > Requirements & Plugins
(`interface/repo_settings/requirements_and_plugins_page.py`): enabling a
plugin with unmet requirements prompts to enable those too; disabling a
plugin something else still requires prompts a "this will break X" warning.
`discover_plugins`/`apply_plugins` themselves never read or enforce it —
a plugin missing its requirement still loads and registers fine, it just
won't have been offered as enabled together automatically outside that one
settings page.

`entry_point` (conventionally `plugin.py`) needs exactly one function:
```python
def register(api) -> None:
    ...
```
Called once at app startup (`core/extensibility/loader.py`'s
`apply_plugins`), after every plugin has been discovered but with **no
guaranteed order** between plugins — don't write a `register(api)` that
assumes another specific plugin has already run. A broken `register(api)`
(raises, or the module has no `register` at all) is caught and recorded as
a `PluginLoadFailure`, not a crash.

## Multi-file plugins: real sibling imports, not `importlib` tricks

A single-file plugin (`software_linker`) just imports from `interface.*`/
`core.*` — nothing to coordinate. A **multi-file** plugin (`explorer`,
`submit` — each 6-8 files) needs its own files to import each other too.
The loader only ever imports the `entry_point` file directly (via
`importlib.util.spec_from_file_location`, a standalone load) — but that
entry file's own `import` statements are resolved normally, so a
multi-file plugin folder is set up as a **real,
plain Python package**: an empty `__init__.py` in the plugin's own folder
(plus one in `plugins/`, `plugins/core/`, and `plugins/repo_internal/`
themselves, already present), so sibling files import each other with
ordinary absolute imports — `from plugins.core.explorer.browser_widget
import RepoBrowserWidget`, not a relative import (the entry file's own
`__name__` isn't `plugins.core.explorer.plugin`, so `from
.browser_widget import ...` would not work — see
`plugins/core/explorer/plugin.py` for the working pattern). Note this
convention doesn't extend to `cache/plugins/` — a repo plugin isn't
guaranteed to live under `plugins/` at all (that's the whole point), so
its own sibling files should import via `Path(__file__).resolve().parent`
relative lookups instead, not a `plugins.*` dotted path (see
`cache/plugins/mGear/plugin.py`'s `tool_root` for the pattern). This is
scoped to *your own plugin's* files — reaching into another plugin's
package this way is still not a thing to do; see "Sharing data with
another plugin" below instead.

## `api` — what `register(api)` receives

`api` is a `PluginAPI` instance (`interface/plugin_api.py`):
- `api.metadata` — `MetadataStore` (the Project/Repo registry).
- `api.programs` — the shared Program catalog (`ProgramStore`);
  `.get_program(id)` raises `core.exceptions.NotFoundError`, not
  `None`/`KeyError`.
- `api.local_config` — per-machine `LocalConfigStore`.
- `api.git` — `GitService`.
- `api.file_opener_registry` — read access to the `FileOpenerRegistry`
  (for a page that needs to call `find_opener()` itself, like Explorer's
  `RepoBrowserPage`) — separate from `api.register_file_opener(...)`,
  which *contributes* an opener rather than reading the registry.
- `api.app_root` — `Path` to the UkoreHub install root, for referencing
  your own plugin's files without guessing nesting depth from `__file__`
  (e.g. `api.app_root / "data" / "icons"`).
- `api.plugin_config_store(plugin_id, *, shared: bool)` — namespaced JSON
  settings (see below).
- `api.register_section(spec)` — a full top-level tab in `SectionRegistry`
  (Explorer/Submit/About today — see `interface/section_registry.py`'s
  `SectionSpec`, including the optional `background_threads` and `wire`
  fields for shutdown cleanup and app-level signal wiring). Set
  `persistent=True` for a section that should be permanently docked
  visible instead of a normal switchable sidebar row/tab — a rare need,
  currently only `plugins/core/project_editor/` (see that plugin's
  README and `interface/main_window.py`'s `_build_main_ui`).
  `trailing_widget_factory` is a further optional field — a small widget
  built once and shown at the right edge of this section's own sidebar row
  (e.g. `plugins/core/Notification/`'s unread-count badge); the plugin
  keeps its own reference to the returned widget and updates it directly,
  `SectionTabList` only lays it out. A general status-widget slot, not
  Notification-specific.
- `api.register_settings_tab`, `api.register_file_opener`,
  `api.register_git_hook` — the remaining registries.

## Sharing data with another plugin: `plugin_config_store`, not imports

`api.plugin_config_store(plugin_id, shared=True|False)` returns a
`PluginConfigStore` — free-form JSON, namespaced by `plugin_id`. Two
unrelated plugins that independently construct a store with the **same
`plugin_id` string** share the same file — no coupling, no import, just
agreeing on a string and a JSON shape in advance. `shared=True` writes to
the git-tracked studio config dir; `shared=False` writes to the gitignored
per-machine dir. `plugins/repo_internal/maya_launcher/plugin.py` reading
`plugins/core/software_linker`'s per-machine `maya.exe` path via
`api.plugin_config_store("software_linker", shared=False)` is the real
worked example, without importing SoftwareLinker's code at all.

## `SectionSpec.wire`/`SectionHost`: cross-plugin UI coordination, not imports

If one plugin's page needs to trigger a specific behavior in another
plugin's page (e.g. Submit's "Inspect in Explorer" jumping to Explorer and
focusing a file), don't import the other plugin's page type. Use:
- A plain string `SectionRegistry` key (e.g. `"repo_browser"`) — stable,
  documented in the target plugin's own `README.md`, and doesn't fail your
  `register(api)` if the other plugin is ever missing/broken.
- An optional protocol method on the target page (e.g.
  `browse_to_path(path)`, mirroring the existing `set_repo()` convention
  every page already implements) — `SectionHost.navigate_and_focus(key,
  path)` (`interface/section_registry.py`) calls it generically via
  `getattr`/`callable`, without `interface/main_window.py` or your plugin
  needing to import the target page's type. See
  `plugins/core/submit/plugin.py`'s `_wire` for the working example.

## Testing

`plugin.py` files aren't reachable by normal `import` in a pytest test
*from outside their own package* (the loader always imports the
`entry_point` standalone via `importlib.util.spec_from_file_location`,
regardless of whether the folder is also a real package internally). If
`register(api)` or a helper is worth covering:
- Pure, Qt-free logic → extract it into a real `core/` module and test it
  normally.
- Logic that only makes sense inside the plugin → verify with a throwaway
  scratchpad script that loads the module the same way the real loader
  does.
