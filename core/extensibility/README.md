# core/extensibility/

The plugin discovery and hook system. No PySide6/Qt imports here —
`hooks.py` deliberately isn't a `QObject` so `core/` stays importable and
testable without a `QApplication`; UI-facing registration (sections,
settings tabs, project-info tabs) is composed on top of these in
`interface/plugin_api.py`, which is the actual `api` object a plugin's
`register(api)` receives.

- `loader.py` — `discover_plugins(roots, api_version)` scans manifest.json +
  entry-point Python files under a list of root directories (`plugins/core`,
  `plugins/repo_internal`, `cache/plugins`) and imports each one;
  `apply_plugins(discovered, api)` calls each one's `register(api)`. Never
  raises — a broken plugin is recorded as a `PluginLoadFailure` and
  skipped, not a crash. Also has `plugin_source()`, returning `"core"`/
  `"repo_internal"` for the two bundled roots, or `"repo"` for a
  `cache/plugins/` entry (its own separate git clone). `launcher.py`
  collects `core_plugin_ids` (every plugin `plugin_source()` returns
  `"core"` for) and passes it to `MainWindow`, whose
  `_apply_plugin_visibility` force-shows every one of those sections for
  every repo, no per-repo opt-out at all (2026-08-04 — there used to be a
  `PluginManifest.core: bool` manifest flag singling out just
  `plugins/core/project_editor/` for this; removed once the same
  always-visible treatment was extended to the whole `plugins/core/` root,
  making the flag redundant). Separately, `launcher.py` also collects
  `opt_in_plugin_ids` (every plugin `plugin_source()` returns
  `"repo_internal"`/`"repo"` for) and passes it to `MainWindow` too —
  `_apply_plugin_visibility` uses it for the opposite (opt-in) gating,
  keyed off `Repo.required_plugin_ids`. See "Plugins" below for the full
  two-way visibility split.
- `config_store.py` — `PluginConfigStore`: namespaced, atomic-write JSON
  settings for a single plugin (mirrors `LocalConfigStore`/`SystemConfigStore`
  in `core/store.py`, but with a free-form key/value schema instead of fixed
  fields).
- `hooks.py` — `GitHookEvent`/`GitHookContext`/`HookRegistry`: plain-Python
  pub/sub for git lifecycle events (before/after clone/pull/push/commit),
  fired from `core/git_service.py`.
- `file_opener.py` — `FileOpenerSpec`/`FileOpenerRegistry`: lets a plugin
  claim responsibility for opening certain file extensions (e.g. launching
  Maya with custom env vars instead of the OS default association) when a
  file is opened through Repo Browser (double-click in the file table) —
  never for files opened outside UkoreHub entirely.
- `debug_log.py` — `register_source`/`log`/`entries`/`sources`/
  `add_listener`/`remove_listener`/`clear`: an in-memory, cross-plugin
  debug log bus, added 2026-07-20 alongside `plugins/core/DebugConsole/`
  (that plugin's own README has the full story — this file is just the
  Qt-free data side of it). Any plugin/core code can call
  `log(source, message)` directly (import the module, no `api` handle
  needed) from anywhere at runtime, not just inside `register(api)` —
  the same "construct/reach directly, convention not import" pattern
  `config_store.py`'s `PluginConfigStore` already relies on elsewhere in
  this codebase. Not persisted (ephemeral, cleared on app restart or via
  DebugConsole's "Clear" button) and capped at 1000 entries.
- `notification_bus.py` — `NotificationEntry`/`push`/`entries`/
  `entries_for`/`add_listener`/`remove_listener`/`clear`: the same
  in-memory, cross-plugin, no-`api`-handle-needed bus pattern as
  `debug_log.py` above, added 2026-08-03 alongside
  `plugins/core/Notification/` (that plugin's own README has the full
  socket/template contract — this file is just the Qt-free data side of
  it). `push(source, project_id, repo_id, label, ...)` is the "template"
  contract: `repo_id=None` means the notification applies to every repo in
  the project, a specific repo id scopes it to just that repo — the
  producer picks this at push time, there is no user-facing scope toggle.
  Not persisted, same reasoning as `debug_log.py` (a notification's
  `on_click` is a live Python callback that can't survive an app restart
  anyway) and capped at 500 entries.

None of these six files import each other. `hooks.py` and `file_opener.py`
import `core.models` (for `Project`/`Repo`); `config_store.py` imports
`core.store._atomic_write`; `debug_log.py`/`notification_bus.py` have no
internal imports at all. All are absolute imports to modules that live
directly in `core/`, not in this subpackage.

## Plugins

`plugins/core/`, `plugins/repo_internal/`, and `cache/plugins/` are
UkoreHub's own sub-systems — implemented once, loaded (or not, on
failure) once at app startup for every project alike (`cache/plugins/`
entries too, once cloned — see `plugins/README.md`). Which of the three
a plugin lives in decides its per-repo sidebar-section visibility
(`interface/repo_settings/requirements_and_plugins_page.py`,
`interface/main_window.py`'s `_apply_plugin_visibility`) — a per-repo
*visibility* toggle, not a per-repo *load* toggle:
- `core/` — always visible, no per-repo opt-out at all (2026-08-04).
  Reserve this root for universal app-level functionality only —
  anything a repo might reasonably want turned off belongs in
  `repo_internal/` instead.
- `repo_internal/` and `cache/plugins/` — hidden by default; a repo must
  opt **in** via `Repo.required_plugin_ids` for the section to show at
  all.
