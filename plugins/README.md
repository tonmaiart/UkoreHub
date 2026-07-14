# plugins/

UkoreHub's own always-on sub-systems — active for **every** project, all the
time, with no per-repo toggle. Contrast with `add-on/` (repo-scoped, opt-in
via `Repo.enabled_addon_ids`) — see `core/extensibility/README.md` for the
full Plugins-vs-Add-ons writeup if you haven't read it yet. This file is the
"how do I write one" guide; that one is the "how does discovery/loading
work" reference.

Two roots, both scanned by the same `discover_plugins()`:
- `studio/` — git-tracked, shared with the whole team (distributed via
  `self_update.py`'s whole-tree `git pull`, same as `data/programs.json`).
  Explorer, Submit, and Software Linker all live here.
- `local/` — gitignored, per-machine/experimental. Use this while
  prototyping a plugin you don't want to commit yet.

## Working on a single plugin — stay inside its folder

When a task names a specific plugin (or the target path is under
`plugins/studio/<Name>/`/`plugins/local/<Name>/`), read and edit **only
that folder**. Don't open a sibling plugin "just in case" — each one is
independent, and reading one has zero information value for working on a
different one (same reasoning as `add-on/`'s folders — see
`add-on/README.md`). Check the plugin's own `README.md` first if it has one
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
plugins/studio/YourPluginName/
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
  "description": "One sentence describing what this plugin registers."
}
```
`id` must be globally unique across every plugin *and* add-on (both share
one discovery namespace). `api_version` must match the app's current
`PLUGIN_API_VERSION` (`interface/plugin_api.py`) or your plugin is skipped
with a `PluginLoadFailure`, not a crash.

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
`importlib.util.spec_from_file_location`, a standalone load, same mechanism
`add-on/` uses) — but that entry file's own `import` statements are
resolved normally, so a multi-file plugin folder is set up as a **real,
plain Python package**: an empty `__init__.py` in the plugin's own folder
(plus one in `plugins/` and `plugins/studio/` themselves, already present),
so sibling files import each other with ordinary absolute imports —
`from plugins.studio.explorer.browser_widget import RepoBrowserWidget`, not
a relative import (the entry file's own `__name__` isn't
`plugins.studio.explorer.plugin`, so `from .browser_widget import ...`
would not work — see `plugins/studio/explorer/plugin.py` for the working
pattern). This is scoped to *your own plugin's* files — reaching into
another plugin's package this way is still not a thing to do; see "Sharing
data with another plugin" below instead.

## `api` — what `register(api)` receives

`api` is a `PluginAPI` instance (`interface/plugin_api.py`), the exact same
object every add-on gets too:
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
  fields for shutdown cleanup and app-level signal wiring).
- `api.register_settings_tab`, `api.register_repo_addon_panel`,
  `api.register_file_opener`, `api.register_git_hook` — the remaining
  registries, shared with add-ons too.

## Sharing data with another plugin: `plugin_config_store`, not imports

`api.plugin_config_store(plugin_id, shared=True|False)` returns a
`PluginConfigStore` — free-form JSON, namespaced by `plugin_id`. Two
unrelated plugins that independently construct a store with the **same
`plugin_id` string** share the same file — no coupling, no import, just
agreeing on a string and a JSON shape in advance. `shared=True` writes to
the git-tracked studio config dir; `shared=False` writes to the gitignored
per-machine dir. `add-on/MayaLauncher/plugin.py` reading
`plugins/studio/software_linker`'s per-machine `maya.exe` path via
`api.plugin_config_store("software_linker", shared=False)` is the real
worked example — see `add-on/README.md`'s "Sharing data with another
add-on" section (the convention is identical for plugins and add-ons).

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
  `plugins/studio/submit/plugin.py`'s `_wire` for the working example.

## Testing

Same as `add-on/`: `plugin.py` files aren't reachable by normal `import` in
a pytest test *from outside their own package* (the loader always imports
the `entry_point` standalone via `importlib.util.spec_from_file_location`,
regardless of whether the folder is also a real package internally). If
`register(api)` or a helper is worth covering:
- Pure, Qt-free logic → extract it into a real `core/` module and test it
  normally.
- Logic that only makes sense inside the plugin → verify with a throwaway
  scratchpad script, same pattern as `add-on/README.md`'s Testing section
  describes.
