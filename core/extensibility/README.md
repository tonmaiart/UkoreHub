# core/extensibility/

The plugin/add-on discovery and hook system. No PySide6/Qt imports here —
`hooks.py` deliberately isn't a `QObject` so `core/` stays importable and
testable without a `QApplication`; UI-facing registration (sections,
settings tabs, project-info tabs, repo-addon panels) is composed on top of
these in `interface/plugin_api.py`, which is the actual `api` object a
plugin's or add-on's `register(api)` receives.

- `loader.py` — `discover_plugins(roots, api_version)` scans manifest.json +
  entry-point Python files under a list of root directories (e.g.
  `plugins/studio`, `plugins/local`, or the separate `add-on/` catalog) and
  imports each one; `apply_plugins(discovered, api)` calls each one's
  `register(api)`. Never raises — a broken plugin/add-on is recorded as a
  `PluginLoadFailure` and skipped, not a crash. Also has `plugin_source()`,
  deriving `"studio"`/`"local"`/`"add-on"` from a discovered plugin's path.
  `PluginManifest.core: bool` (manifest.json `"core": true`, default
  `false`, added 2026-07-15) flags a plugin as load-bearing for per-repo
  *visibility* — distinct from `PluginLoadFailure` isolation, which still
  applies the same to a core plugin if it fails to import/register.
  `launcher.py` collects `core_plugin_ids` from this flag and passes it to
  `MainWindow`, whose `_apply_plugin_visibility` force-shows a core
  plugin's section regardless of a repo's `active_plugin_ids` allowlist —
  and `interface/settings/enable_plugin_page.py` renders it checked and
  disabled so a manager can't accidentally hide it in the first place. The
  first (and so far only) user is `plugins/studio/project_editor/`: hiding
  it for a repo would remove the only way to switch that repo's active
  repo at all, a real lockout rather than a preference.
- `config_store.py` — `PluginConfigStore`: namespaced, atomic-write JSON
  settings for a single plugin (mirrors `LocalConfigStore`/`SystemConfigStore`
  in `core/store.py`, but with a free-form key/value schema instead of fixed
  fields).
- `hooks.py` — `GitHookEvent`/`GitHookContext`/`HookRegistry`: plain-Python
  pub/sub for git lifecycle events (before/after clone/pull/push/commit),
  fired from `core/git_service.py`.
- `file_opener.py` — `FileOpenerSpec`/`FileOpenerRegistry`: lets a repo-scoped
  add-on claim responsibility for opening certain file extensions (e.g.
  launching Maya with custom env vars instead of the OS default association)
  when a file is opened through Repo Browser (double-click in the file
  table) — never for files opened outside UkoreHub entirely. Gated by
  `Repo.enabled_addon_ids`, consistent with Add-ons being per-repo opt-in.
- `debug_log.py` — `register_source`/`log`/`entries`/`sources`/
  `add_listener`/`remove_listener`/`clear`: an in-memory, cross-plugin
  debug log bus, added 2026-07-20 alongside `plugins/studio/DebugConsole/`
  (that plugin's own README has the full story — this file is just the
  Qt-free data side of it). Any plugin/add-on/core code can call
  `log(source, message)` directly (import the module, no `api` handle
  needed) from anywhere at runtime, not just inside `register(api)` —
  the same "construct/reach directly, convention not import" pattern
  `config_store.py`'s `PluginConfigStore` already relies on elsewhere in
  this codebase. Not persisted (ephemeral, cleared on app restart or via
  DebugConsole's "Clear" button) and capped at 1000 entries.

None of these five files import each other. `hooks.py` and `file_opener.py`
import `core.models` (for `Project`/`Repo`); `config_store.py` imports
`core.store._atomic_write`; `debug_log.py` has no internal imports at all.
All are absolute imports to modules that live directly in `core/`, not in
this subpackage.

## Plugins vs Add-ons

These are two distinct concepts sharing the same discovery mechanism
(`loader.py`) but different purposes — don't conflate them:

- **Plugins** (`plugins/studio/` + `plugins/local/`) are UkoreHub's own
  sub-systems — implemented once, loaded (or not, on failure) once at app
  startup for every project alike. A repo *can* additionally hide a
  loaded plugin's own sidebar section via `Repo.active_plugin_ids`
  (Settings > Repo > Enable Plugin, `interface/settings/enable_plugin_page.py`)
  — a per-repo *visibility* toggle, not a per-repo *load* toggle — unless
  the plugin is flagged `manifest.json` `"core": true` (`PluginManifest.core`,
  see `loader.py` above), which is never hideable this way.
- **Add-ons** (`add-on/`) are extensions a **repo** opts into. A repo's
  `Repo.enabled_addon_ids` (`core/models.py`, `core/store.py`'s
  `set_repo_enabled_addons`) picks which discovered add-ons apply to that
  repo, edited in Project Editor. Because that field lives in the
  shared `data/projects.json`, **enabling or disabling an add-on for a repo
  affects every user working on that repo** — it is not a personal/local
  toggle.
- Both are loaded via the exact same `discover_plugins()`/`apply_plugins()`
  machinery and get the exact same `PluginAPI` capabilities in
  `register(api)` — the only difference is which root folder they're
  discovered from and how a repo relates to them (always-on vs. opt-in).
- Some plugins/add-ons may declare a requirement on other plugins/add-ons
  (e.g. an add-on that needs a specific plugin loaded first) — there is
  **no enforcement mechanism for this yet**; it's a documented future
  concern, not implemented.
- **No local add-ons policy exists yet.** Unlike `plugins/` (which splits
  into a git-tracked `studio/` and gitignored `local/`), `add-on/` is a
  single flat folder — everything in it is git-tracked/shared. Do not add an
  `add-on/local/` split without an explicit decision to do so.
