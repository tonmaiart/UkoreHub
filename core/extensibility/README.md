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
  when a file is opened through Repo Browser or the sidebar's Recent Files —
  never for files opened outside UkoreHub entirely. Gated by
  `Repo.enabled_addon_ids`, consistent with Add-ons being per-repo opt-in.

None of these four files import each other. `hooks.py` and `file_opener.py`
import `core.models` (for `Project`/`Repo`); `config_store.py` imports
`core.store._atomic_write`. All are absolute imports to modules that live
directly in `core/`, not in this subpackage.

## Plugins vs Add-ons

These are two distinct concepts sharing the same discovery mechanism
(`loader.py`) but different purposes — don't conflate them:

- **Plugins** (`plugins/studio/` + `plugins/local/`) are UkoreHub's own
  sub-systems — implemented once, active for **every** project, all the
  time. They are not something a user toggles on or off per repo; there's no
  "enabled plugins" concept, only "loaded or not" at app startup.
- **Add-ons** (`add-on/`) are extensions a **repo** opts into. A repo's
  `Repo.enabled_addon_ids` (`core/models.py`, `core/store.py`'s
  `set_repo_enabled_addons`) picks which discovered add-ons apply to that
  repo, edited in Project Data Editor. Because that field lives in the
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
