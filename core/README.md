# core/

Non-UI logic layer for UkoreHub — no PySide6/Qt imports here. Everything the
`interface/` layer depends on for data and git operations lives in this
folder, organized into five domain sub-packages plus a flat handful of
app-wide primitives.

**Working here:** stay inside `core/` unless the change requires updating
an `interface/` call site — don't open `interface/` files otherwise. Each
sub-package below has its own README — check it first if you're working in
one:

- **`storage/`** — the JSON-file stores (`MetadataStore`, `LocalConfigStore`,
  `SystemConfigStore`) and their shared atomic-write helper. See
  `core/storage/README.md`.
- **`auth/`** — token storage and login helpers (GitHub, Google). See
  `core/auth/README.md`.
- **`vcs/`** — git subprocess wrapper, GCS cloud sync, GitHub REST helpers,
  repo path resolution. See `core/vcs/README.md`.
- **`events/`** — the hook registry and the two in-memory event buses
  (debug log). See `core/events/README.md`.
- **`extensibility/`** — plugin discovery, per-plugin config storage, file
  opener registration. See `core/extensibility/README.md`.

`app_core.py`'s `UkoreCore` is the composition facade that ties the
sub-packages' stateful services together into one object — `launcher.py`
constructs one `UkoreCore` instance and threads it into `MainWindow`/
`PluginAPI` instead of wiring each service individually. It deliberately
never imports `core.vcs.cloud_sync` (see that module's own docstring and
`core/vcs/README.md` for why) — cloud pull/push orchestration and the
mandatory GitHub-login gate stay in `launcher.py`.

Everything else stays flat here since it doesn't form a natural cluster
beyond "core infrastructure":

- `models.py` — dataclasses for `Project` (including `programs:
  list[Program]`, that Project's own Program Database — pipeline software
  like "Autodesk Maya" a repo can list as a requirement, **not** shared
  with other Projects), `Repo` (including `browser_links:
  list[BrowserLink]`, repo-scoped bookmarks rendered as dynamic Sidebar
  rows that open externally — see `interface/browser_links/README.md`),
  `RepoStatus`, etc.
- `os_utils.py` — OS-level helpers (open in file explorer, open with default
  app).
- `relaunch.py` — `relaunch_ukorehub_exe(repo_root)`: spawns `UkoreHub.exe`
  detached with PyInstaller's `_PYI_*` onefile bootloader env vars stripped
  (see bug-history 2026-08-04 for why a bare `subprocess.Popen` here
  crashes the new process). Shared by `interface/main_window.py`'s
  `_relaunch_to_login` (logout) and `launcher.py`'s own mandatory login
  gate (refuses to open the main window without a cached token) — the one
  place that knows how to spawn `UkoreHub.exe` safely from within a
  running UkoreHub process.
- `exceptions.py` — shared exception types (`UkoreHubError`, `ValidationError`,
  `NotFoundError`, `ConflictError`, `GitOperationError`, `GitHubAuthError`,
  `GoogleAuthError`).
- `version.py` — app name/version constants.
- `app_core.py` — see above.

Note: `Repo.active_plugin_ids` (`set_repo_active_plugin_ids`) is no longer
read anywhere (2026-08-04 — every `plugins/core/` plugin is
unconditionally visible for every repo now, see
`interface/main_window.py`'s `_apply_plugin_visibility`); the field is
kept purely so existing persisted JSON with this key still round-trips
cleanly. `Repo.required_plugin_ids` (`set_repo_required_plugin_ids`) is
the real UI-visibility gate now, for `plugins/repo_internal/` and
`cache/plugins/` entries — hides a plugin's sidebar section unless the
repo's `required_plugin_ids` lists that plugin's id. Edited via
Settings > (repo) > Requirements & Plugins
(`interface/repo_settings/requirements_and_plugins_page.py`).

A second field, `Repo.browser_links` (`set_repo_browser_links`,
`core/models.py`'s `BrowserLink`) is a different shape again: each entry
becomes its own **dynamic sidebar row** while the owning repo is active,
rebuilt from scratch on every repo switch by `interface/main_window.py`'s
`_rebuild_dynamic_tabs` — clicking one opens the link in the OS's default
browser (`QDesktopServices.openUrl`), not an embedded page (see
`interface/browser_links/README.md`). Edited via Settings > Repo Setting
(Dev) > Browser. Unlike
`active_plugin_ids`, this doesn't hide anything that exists elsewhere — it
*adds* tabs that only exist because the link record does. (A sibling
Explorer-pin mechanism used to work the same way — `Repo.explorer_pins`/
`ExplorerPin` — but Add-Pinned-Repo was removed as no longer needed; see
git history if it needs to come back.)
