# core/extensibility/

Plugin discovery and per-plugin config storage. No PySide6/Qt imports here
— UI-facing registration (sections, settings tabs, project-info tabs) is
composed on top of these in `interface/plugin_api.py`, which is the actual
`api` object a plugin's `register(api)` receives.

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
  in `core/storage/config_store.py`, but with a free-form key/value schema
  instead of fixed fields). Also `ProjectPluginConfigStore`: same `get`/`set`
  contract, but backed by the currently active `Project.plugin_data`
  (`core/models.py`) instead of its own JSON blob — for plugin data that's
  inherently session/project-scoped rather than studio-wide (e.g.
  `maya_launcher`'s env-var bridge). See `interface/plugin_api.py`'s
  `project_plugin_config_store()` and `plugins/README.md`. Uses
  `core/storage/atomic_file.py`'s `atomic_write` — the one file in this
  folder with a dependency on another `core/` sub-package.
- `file_opener.py` — `FileOpenerSpec`/`FileOpenerRegistry`: lets a plugin
  claim responsibility for opening certain file extensions (e.g. launching
  Maya with custom env vars instead of the OS default association) when a
  file is opened through Repo Browser (double-click in the file table) —
  never for files opened outside UkoreHub entirely.

The hook registry (`hooks.py`) and the in-memory event bus
(`debug_log.py`) that used to live in this folder
moved to `core/events/` (2026-08-09 reorg) — see `core/events/README.md`.

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
