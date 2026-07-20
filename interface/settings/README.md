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
  (`os.execv(sys.executable, [sys.executable, *sys.argv])`)
  `plugins/studio/self_updater/`'s "Update and Restart" button uses too,
  just without the `self_update.pull_update()` git pull first).
  `CATEGORY_GENERAL`.
- `github_oauth_settings_page.py` — `GithubOAuthSettingsPage`: just the
  GitHub OAuth Client ID field, split out of `common_settings_page.py`
  since it's studio-admin plumbing most users never touch.
  `CATEGORY_DEVELOPER`.
- `program_database_page.py` — CRUD for the shared Program Database
  (`core/program_store.py`), using `program_dialog.py`'s `ProgramDialog`
  for add/edit. `CATEGORY_DEVELOPER`.
- `program_dialog.py` — `ProgramDialog`: name/version/description/icon
  editor for one `Program`, used only by `program_database_page.py`.
- `plugin_catalog_page.py` — read-only listing of what got discovered
  under `plugins/`. `CATEGORY_DEVELOPER`.

**Moved out 2026-07-20** (domain-based reorg — grouped by "kind of Settings
tab" here even though each is really its own feature domain):
`browser_links_settings_page.py` → `interface/browser_links/` (alongside
the Browser Link runtime tab it configures — see that folder's `README.md`);
`local_repository_page.py`/`enable_plugin_page.py` →
`interface/repo_settings/` (the repo-configuration domain, distinct from
this folder's remaining app/machine-level tabs — see that folder's
`README.md`). Both are still registered into the same
`SettingsTabRegistry` from `interface/builtin_settings_tabs.py`, still
`CATEGORY_REPO`, still rendered by
`plugins/studio/project_editor/repo_settings_panel.py` — only where their
source files live changed.

**No longer rendered here at all:** as of 2026-07-15, `SettingsView` stops
rendering `CATEGORY_REPO` entirely — every `CATEGORY_REPO` tab (Browser,
Local Repository, Enable Plugin, plus `project_editor`'s own Custom Paths)
now renders as a grouped tab list inside
`plugins/studio/project_editor/`'s "Repository Setting" popup instead,
read generically off the same `SettingsTabRegistry`
(`category == CATEGORY_REPO`) — see that plugin's `repo_settings_panel.py`.
The tabs themselves are unchanged and still registered exactly as below —
only which container renders them changed. "Project Data Editor" (full
CRUD for the whole Project/Repo registry, formerly `CATEGORY_DEVELOPER`)
moved out to `plugins/studio/project_editor/` the same day, now as a
node-graph top-level section rather than a Settings tab — see that
plugin's README. "Project Status" (read-only per-repo clone/sync status
tree, `CATEGORY_REPO`) was removed entirely 2026-07-20 — no longer needed.

**Removed:** `addon_settings_page.py`/`AddonSettingsPage` (the "Add-ons"
tab) — deprecated and removed as of 2026-07-14. It used to be the only UI
for editing a discovered add-on's icon/description override/required
Program(s) (`core/addon_store.py`'s `AddonMetadataStore`); no replacement
UI exists yet, see `add-on/README.md`'s "Icon, description override, and
required Program" section.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `shared/` addition, or touches `main_window.py`'s
wiring (which opens `SettingsDialog` via `Sidebar.settings_requested`).
