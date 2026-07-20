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

## Working on a single add-on — stay inside its folder

When a task names a specific add-on (or the target path is under
`add-on/<Name>/`), read and edit **only that folder**. Don't open sibling
add-ons "just in case" — each one is an independent, often-large, often
vendored tool tree (e.g. `DreamwallPicker/maya-scripts/dwpicker/` alone is
dozens of files) with zero information value for working on a different
one. Check the add-on's own `README.md` first if it has one (same
folder-README convention as `core/`/`interface/` — see root `CLAUDE.md`).

If a task genuinely needs data from another add-on, that's almost always
the shared-`plugin_config_store` convention below (a plugin_id string + a
documented JSON shape), not a reason to read the other add-on's source. The
one real exception is explicit cross-add-on debugging ("why doesn't
MayaLauncher pick up UkoreBrowser's contribution") — say so and read both
deliberately, rather than defaulting to broad exploration for a
single-add-on task. See the `ukorehub-addon` skill for the fuller writeup.

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
  "description": "One sentence — shown in the repo editor's add-on picker."
}
```
`id` must be globally unique across every plugin *and* add-on (both share
one discovery namespace) and is what you'll use everywhere else — as the
key in `Repo.enabled_addon_ids`, the argument to `api.register_*`, and the
`AddonMetadataStore` key (see below). `api_version` must match the app's
current `PLUGIN_API_VERSION` (`interface/plugin_api.py`) or your add-on is
skipped with a `PluginLoadFailure`, not a crash. As of 2026-07-14 the
Settings > Add-ons tab (the only UI surface that showed add-on load
failures/catalog) was removed as deprecated — check
`core/extensibility/loader.py`'s `discover_plugins(...).failures` result
directly (e.g. from a throwaway script) if your add-on silently isn't
showing up. Settings > Developer > Plugins (`plugin_catalog_page.py`)
still exists but only ever reflected the `plugins/` root's own discovery
result, not `add-on/`'s.

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
is caught and recorded as a `PluginLoadFailure`, not a crash (see the note
above — there's no dedicated UI surface for add-on load failures anymore).

## `api` — what `register(api)` receives

`api` is a `PluginAPI` instance (`interface/plugin_api.py`), the exact same
object every plugin gets too. The two calls specific to repo-scoped add-on
behavior:

- `api.register_file_opener(addon_id, extensions, opener)` — claims
  responsibility for opening certain file extensions (e.g. launching an
  app with custom env vars) instead of the OS default association, when a
  file is opened through Repo Browser (double-click in the file table).
  `opener(path, repo) -> bool` returns whether it handled the file. **Only
  reachable when the active repo has `addon_id` in `Repo.enabled_addon_ids`** —
  `core/extensibility/file_opener.py`'s `FileOpenerRegistry` enforces this,
  so there's no risk of your opener firing for files opened outside
  UkoreHub or on a repo that hasn't enabled you.
- `api.register_repo_addon_panel(addon_id, panel_factory)` — registers a
  status widget (`panel_factory(repo) -> QWidget`) for this add-on, shown
  whenever it's enabled for the active repo. **Currently has no UI host**:
  the Repo About tab that used to render these panels as sub-tabs was
  removed 2026-07-20, and nothing else consumes this registry yet — a
  panel registered here is stored but never displayed. Skip this call
  until a new host exists.

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
  `api.register_settings_tab` — same registries plugins use; an add-on can
  register any of these too, though it's less common (most add-ons only
  need the two above).

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

A real, worked example of the "consumer reads another plugin's config"
half of this convention: `plugins/studio/maya_launcher/plugin.py` reads
`plugins/studio/software_linker`'s per-machine `maya.exe` path via
`api.plugin_config_store("software_linker", shared=False)`, without
importing SoftwareLinker's code at all — see `plugins/README.md`'s
"Sharing data with another plugin" section (the convention is identical
whether both sides are plugins, both are add-ons, or one of each).

**As of 2026-07-14, `add-on/` has no folders** — its previous 10 entries
were consolidated: `MayaLauncher` plus 7 add-ons that existed only to feed
a shared `maya_launcher_env_bridge` config (`AdvancedSkeleton`,
`MayaNgskin`, `MayaToolkit`, `mGear`, `UkoreBrowser`, `DreamwallPicker`,
`StudioLibrary`) all moved into one `plugins/studio/maya_launcher/` plugin
(see that plugin's own README for why — none of the 7 contributors ever
registered anything besides that one bridge write, so the "many
independent add-ons sharing one bridge, order-independent" pattern that
used to be this section's second worked example no longer has a live
example in this codebase). `BlenderLauncher`/`UnrealLauncher` were removed
outright — neither had a real `manifest.json`/`plugin.py`. The pattern
itself is still valid for a genuine multi-add-on scenario; write a new
worked example here the next time one exists.

## Icon, description override, and required Program — not in code

`manifest.json`'s `name`/`description` are the fallback shown until
overridden in `core/addon_store.py`'s `AddonMetadataStore` →
`data/addon_settings.json` (shared/git-tracked). As of 2026-07-14 there is
no Settings UI for editing this file — it was the deprecated Settings →
Add-ons tab, now removed; editing an add-on's icon/description override or
required Program(s) means writing to `data/addon_settings.json` directly
(or through `AddonMetadataStore`'s own methods from a script) until/unless
a replacement UI exists. An add-on's **required Program(s)** (e.g. "this
add-on requires Autodesk Maya") is deliberately *not* a manifest field or
something `register(api)` sets, so studio admins can retarget an add-on to
a different/renamed Program catalog entry without a code change. Declaring a
required program is what makes an add-on nest under that program's node in
the repo editor's add-on picker (`RequirementsTreeWidget`, using
`core/addon_store.py`'s `group_addon_ids_by_program`) — an add-on with no
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
