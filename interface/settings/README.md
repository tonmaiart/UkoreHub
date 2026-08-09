# interface/settings/

Mostly the "Setting" popup — opened via the icon-only Setting button in
Sidebar's footer (app-level, not one of the repo-scoped `SectionTabList`
rows). Every `SettingsTabSpec` page in that popup **self-persists on every
change** — there is no Save/Cancel step; `SettingsTabSpec` has no
`on_save`/`on_cancel` hooks. The one exception to that self-persisting
convention — `StudioSettingsDialog`, its own separate window with a real
login gate and an explicit Save button — no longer lives in this folder:
it moved to `plugins/core/CloudConfig/studio_settings_dialog.py`, opened
via a "Studio" footer button that plugin contributes through
`SidebarFooterActionRegistry` rather than a hardcoded Sidebar button. See
that plugin's own README for why.

- `settings_view.py` — `SettingsView` (a top-level `QTabWidget` with three
  categories) + `SettingsDialog` (the popup wrapper around it, reverted
  2026-07-19 back to a dialog, matching this app's own pre-registry
  history; briefly an embedded `MainWindow.view_stack` page in between,
  see `SettingsDialog`'s own docstring). `MainWindow._on_settings_requested`
  constructs a fresh `SettingsDialog` on every open — no state carried
  between opens, same convention `register_builtin_settings_tabs`'
  docstring documents for every tab's `page_factory`. `SettingsView` itself
  is driven by `interface/settings_tab_registry.py`'s `SettingsTabRegistry`
  (open, ordered — built-in and plugin-provided tabs register into the
  same collection, see `interface/builtin_settings_tabs.py`). Renders three
  top-level tabs, each a `_CategoryPage` — **Account**
  (`CATEGORY_GENERAL`), **Project (Dev)** (`CATEGORY_PROJECT` +
  `CATEGORY_DEVELOPER`, shown as two header groups), and **Repo Setting
  (Dev)** (`CATEGORY_REPO`, split into "Repository"/"Plugins" header
  groups the same way the now-retired `RepoSettingsPanel` used to). A
  `_CategoryPage` that resolves to exactly one `SettingsTabSpec` shows that
  page directly with no tab-list chrome at all (Account today) — see that
  class's own docstring.
  `get_tab_widget(key)` is the one public escape hatch for reaching a
  specific constructed page from outside — `main_window.py` uses it (via
  `SettingsDialog.view.get_tab_widget(...)`) to connect
  `CommonSettingsPage.logout_requested` (also closing the dialog itself,
  since logout closes the whole app — see `common_settings_page.py` below)
  and `BrowserLinksSettingsPage.browser_links_changed` without this view
  needing to know what those pages are.
- `common_settings_page.py` — account info (avatar, GitHub username, login
  date — `LocalConfigStore.github_username`/`github_login_at`, the latter
  set in `updater.py (UkoreHubLauncher repo)`'s `_start_login_flow` on every
  successful device-flow login and cleared alongside the username on
  logout/switch-account; the avatar itself is fetched off the UI thread by
  a small `_AvatarFetchWorker(QThread)` calling
  `core/github/auth.py`'s `fetch_avatar_bytes`, the same
  background-thread pattern `plugins/core/explorer/path_commit_history_worker.py`
  uses), workspace folder (read-only), the Logout button
  (`logout_requested` signal, connected in `main_window.py` to
  `_on_logout_requested` — clears the cached token/username/login-date via
  `core/github/token_store.py`'s `TokenStore` and relaunches
  `UkoreHub.exe`, whose own login step, `updater.py (UkoreHubLauncher repo)`,
  shows the GitHub login screen again since the token is now gone; this
  app has no in-app login UI of its own to "go back to" otherwise), and a
  Restart button (`restart_requested` signal, connected to
  `MainWindow._on_restart_requested`, which calls the `_restart_app()`
  helper: `os.execv(sys.executable, [sys.executable, *sys.argv])`).
  `CATEGORY_GENERAL`.
- `github_oauth_settings_page.py` — `GithubOAuthSettingsPage`: just the
  GitHub OAuth Client ID field, split out of `common_settings_page.py`
  since it's studio-admin plumbing most users never touch — still needed
  even though login moved out of this app, since the launcher's own login
  step reads this same `data/system_config.json` value.
  `CATEGORY_DEVELOPER`.
- `program_database_page.py` — `ProgramDatabasePage`: CRUD for the active
  Project's own Program Database (`core/models.py`'s `Project.programs`,
  via `core/store.py`'s `MetadataStore` — each Project has its own, not
  shared). Reads `local_config_store.active_project_id` directly (no
  Project selector of its own anymore — removed as of the single-project-
  per-session change, since that id is now fixed for the whole run by
  `launcher.py`'s mandatory Project Selector gate); uses
  `program_dialog.py`'s `ProgramDialog` for add/edit. `CATEGORY_PROJECT`.
- `program_dialog.py` — `ProgramDialog`: name/version/description/icon
  editor for one `Program`, used only by `program_database_page.py`.
- `plugin_catalog_page.py` — read-only listing of what got discovered
  under `plugins/`. `CATEGORY_DEVELOPER`.

**Moved out 2026-07-20** (domain-based reorg — grouped by "kind of Settings
tab" here even though each is really its own feature domain):
`browser_links_settings_page.py` → `interface/browser_links/` (alongside
the Browser Link runtime tab it configures — see that folder's `README.md`);
`local_repository_page.py`/`requirements_and_plugins_page.py` →
`interface/repo_settings/` (the repo-configuration domain, distinct from
this folder's remaining app/machine-level tabs — see that folder's
`README.md`). Both are still registered into the same
`SettingsTabRegistry` from `interface/builtin_settings_tabs.py`, still
`CATEGORY_REPO` — only where their source files live changed.

**Rendering history:** from 2026-07-15 through this refactor,
`SettingsView` didn't render `CATEGORY_REPO` at all — every `CATEGORY_REPO`
tab rendered instead inside `plugins/core/project_editor/`'s "Repository
Setting" popup (`RepoSettingsPanel`/`RepoSettingsDialog`,
`repo_settings_panel.py`), to avoid the same setting being editable from
two different dialogs. That popup is now retired: `CATEGORY_REPO` tabs
render here again, under the **Repo Setting (Dev)** top tab, and a repo
node's "Repository Setting..." right-click opens this same dialog (via
`UICommandService.open_settings_tab`) instead of a popup of its own — see
`plugins/core/project_editor/project_graph_view.py`'s
`open_repo_settings()`. "Project Data Editor" (full CRUD for the whole
Project/Repo registry, formerly `CATEGORY_DEVELOPER`) moved out to
`plugins/core/project_editor/` back on 2026-07-15, now as a node-graph
top-level section rather than a Settings tab — see that plugin's README.
"Project Status" (read-only per-repo clone/sync status tree,
`CATEGORY_REPO`) was removed entirely 2026-07-20 — no longer needed.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `shared/` addition, or touches `main_window.py`'s
wiring (which opens `SettingsDialog` via `Sidebar.settings_requested`).
