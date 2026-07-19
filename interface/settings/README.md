# interface/settings/

The "Setting" popup — opened via the icon-only Setting button in Sidebar's
footer (app-level, not one of the repo-scoped `SectionTabList` rows). Every
page here **self-persists on every change** — there is no Save/Cancel step
anywhere; `SettingsTabSpec` has no `on_save`/`on_cancel` hooks.

- `settings_view.py` — `SettingsView` (the left-tab-bar shell) +
  `SettingsDialog` (the popup wrapper around it, reverted 2026-07-19 back
  to a dialog — matches Repository Setting's own `RepoSettingsDialog`
  pattern in `plugins/studio/project_editor/repo_settings_panel.py`, and
  this app's own pre-registry history; briefly an embedded
  `MainWindow.view_stack` page in between, see `SettingsDialog`'s own
  docstring). `MainWindow._on_settings_requested` constructs a fresh
  `SettingsDialog` on every open — no state carried between opens, same
  convention `register_builtin_settings_tabs`' docstring documents for
  every tab's `page_factory`. `SettingsView` itself is driven by
  `interface/settings_tab_registry.py`'s `SettingsTabRegistry` (open,
  ordered — built-in and plugin-provided tabs register into the same
  collection, see `interface/builtin_settings_tabs.py`). Renders three
  sections with a non-selectable header row each — **General** (whole-app/
  machine settings) then **Developer** (studio-admin/internal-plumbing
  tabs most users never need) — per each tab's `SettingsTabSpec.category`
  (`CATEGORY_GENERAL`/`CATEGORY_REPO`/`CATEGORY_DEVELOPER`, default
  General). `CATEGORY_REPO` tabs are registered in the same registry but
  are not rendered here (see the "No longer rendered here at all" note
  above) — only `CATEGORY_GENERAL`/`CATEGORY_DEVELOPER` show up in this
  tab list. A blank non-selectable gap row (`_add_gap_row`) separates each
  rendered category group from the next, on top of each header row's own
  padding.
  `get_tab_widget(key)` is the one public escape hatch for reaching a
  specific constructed page from outside — `main_window.py` uses it (via
  `SettingsDialog.view.get_tab_widget(...)`) to connect
  `CommonSettingsPage.logout_requested` (also closing the dialog itself,
  since logout tears down the main UI behind it) and
  `BrowserLinksSettingsPage.browser_links_changed` without this view
  needing to know what those pages are.
- `common_settings_page.py` — workspace folder (read-only), the Logout
  button (moved here from Sidebar's footer — `logout_requested` signal,
  connected in `main_window.py` to the same logout flow the old toggle
  button used to trigger), and a Restart button (added 2026-07-19 —
  `restart_requested` signal, connected to `MainWindow._on_restart_requested`,
  which calls the same `_restart_app()` helper
  (`os.execv(sys.executable, [sys.executable, *sys.argv])`) Sidebar's own
  "Update and Restart" button already used, just without the
  `self_update.pull_update()` git pull first). `CATEGORY_GENERAL`.
- `github_oauth_settings_page.py` — `GithubOAuthSettingsPage`: just the
  GitHub OAuth Client ID field, split out of `common_settings_page.py`
  since it's studio-admin plumbing most users never touch.
  `CATEGORY_DEVELOPER`.
- `program_database_page.py` — CRUD for the shared Program Database
  (`core/program_store.py`), using `program_dialog.py`'s `ProgramDialog`
  for add/edit. `CATEGORY_DEVELOPER`.
- `program_dialog.py` — `ProgramDialog`: name/version/description/icon
  editor for one `Program`, used only by `program_database_page.py`.
- `project_status_page.py` — read-only per-repo clone/sync status tree.
  `CATEGORY_REPO`.
- `browser_links_settings_page.py` — `BrowserLinksSettingsPage`:
  add/rename/remove/change-icon for the active repo's Browser Links
  (`core/models.py`'s `BrowserLink`, `icon_filename` falls back to
  `data/icons/icons8-browser-50.png`) — each shown as its own top-level tab
  elsewhere, see `interface/main_window.py`'s dynamic tab rebuild. Moved
  here from `interface/about/repo_about_page.py`'s "Browser" sub-tab since
  it's a repo *setting*, not repo info. Unlike the other `CATEGORY_REPO`
  tabs it's genuinely scoped to a single repo, so it can't rely on
  `set_repo()` (MainWindow never calls that on Settings pages) — it
  resolves the active project/repo itself from `local_config_store` in
  `refresh()`, called on construction and on `on_activated`.
- `plugin_catalog_page.py` — read-only listing of what got discovered
  under `plugins/`. `CATEGORY_DEVELOPER`.
- `local_repository_page.py` — `LocalRepositoryPage`: shows the active
  repo's local clone status/path and a "Remove Local Repositories" button
  that `shutil.rmtree`s the clone folder (`core/paths.py`'s
  `resolve_repo_path`) and marks the repo `not_cloned`
  (`MetadataStore.mark_status`) — does not touch the Project/Repo registry
  record itself, only the on-disk clone. Same self-resolving-active-repo
  `refresh()` pattern as `browser_links_settings_page.py`. `CATEGORY_REPO`.
- `enable_plugin_page.py` — `EnablePluginPage`: per-repo checkbox list over
  every discovered `plugins/studio`+`plugins/local` entry
  (`Repo.active_plugin_ids`), self-persisting like every other page here.
  **Distinct from Add-ons** (`Repo.enabled_addon_ids`) — see
  `core/README.md`'s note on the difference; unlike Add-ons, unchecking a
  plugin here actually hides its sidebar section for this repo (enforced in
  `interface/main_window.py`'s `_apply_plugin_visibility`, wired via a
  plugin-id-to-section-key map built in `launcher.py`). An empty
  `active_plugin_ids` (the default) means "unrestricted" — every plugin
  stays visible. A plugin flagged `manifest.json` `"core": true`
  (`PluginManifest.core`, e.g. `plugins/studio/project_editor/`) renders
  here checked and disabled — it can never actually be hidden, so there's
  nothing to toggle. `CATEGORY_REPO`.

**No longer rendered here at all:** as of 2026-07-15, `SettingsView` stops
rendering `CATEGORY_REPO` entirely — every `CATEGORY_REPO` tab (Project
Status, Browser, Local Repository, Enable Plugin) now renders as a
collapsible section inside `plugins/studio/project_editor/`'s right panel
instead, read generically off the same `SettingsTabRegistry`
(`category == CATEGORY_REPO`). The tabs
themselves are unchanged and still registered exactly as below — only
which container renders them changed. "Project Data Editor" (full CRUD for
the whole Project/Repo registry, formerly `CATEGORY_DEVELOPER`) moved out
to `plugins/studio/project_editor/` the same day, now as a node-graph
top-level section rather than a Settings tab — see that plugin's README.

**Removed:** `addon_settings_page.py`/`AddonSettingsPage` (the "Add-ons"
tab) — deprecated and removed as of 2026-07-14. It used to be the only UI
for editing a discovered add-on's icon/description override/required
Program(s) (`core/addon_store.py`'s `AddonMetadataStore`); no replacement
UI exists yet, see `add-on/README.md`'s "Icon, description override, and
required Program" section.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `shared/` addition, or touches `main_window.py`'s
wiring (which opens `SettingsDialog` via `Sidebar.settings_requested`).
