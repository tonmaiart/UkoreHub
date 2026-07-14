# interface/settings/

The "Setting" view — shown via the icon-only Setting button in Sidebar's
footer (app-level, not one of the repo-scoped `SectionTabList` rows). Every
page here **self-persists on every change** — there is no Save/Cancel step
anywhere; `SettingsTabSpec` has no `on_save`/`on_cancel` hooks.

- `settings_view.py` — `SettingsView`: the left-tab-bar shell, driven by
  `interface/settings_tab_registry.py`'s `SettingsTabRegistry` (open,
  ordered — built-in and plugin-provided tabs register into the same
  collection, see `interface/builtin_settings_tabs.py`). Renders three
  sections with a non-selectable header row each — **General** (whole-app/
  machine settings), **Repo** (settings about the active repo/project
  data), then **Developer** (studio-admin/internal-plumbing tabs most
  users never need) — per each tab's `SettingsTabSpec.category`
  (`CATEGORY_GENERAL`/`CATEGORY_REPO`/`CATEGORY_DEVELOPER`, default
  General). The Repo header row is relabeled to the active repo's own name
  at runtime (`set_active_repo_name`, called from `main_window.py` on every
  repo switch) — falls back to "REPO" when no repo is active. A blank
  non-selectable gap row (`_add_gap_row`) separates each category group
  from the next, on top of each header row's own padding.
  `get_tab_widget(key)` is the one public escape hatch for reaching a
  specific constructed page from outside — `main_window.py` uses it to
  connect `CommonSettingsPage.logout_requested` and
  `BrowserLinksSettingsPage.browser_links_changed` without this view
  needing to know what those pages are.
- `common_settings_page.py` — workspace folder (read-only) and the Logout
  button (moved here from Sidebar's footer — `logout_requested` signal,
  connected in `main_window.py` to the same logout flow the old toggle
  button used to trigger). `CATEGORY_GENERAL`.
- `github_oauth_settings_page.py` — `GithubOAuthSettingsPage`: just the
  GitHub OAuth Client ID field, split out of `common_settings_page.py`
  since it's studio-admin plumbing most users never touch.
  `CATEGORY_DEVELOPER`.
- `program_database_page.py` — CRUD for the shared Program Database
  (`core/program_store.py`), using `program_dialog.py`'s `ProgramDialog`
  for add/edit. `CATEGORY_DEVELOPER`.
- `program_dialog.py` — `ProgramDialog`: name/version/description/icon
  editor for one `Program`, used only by `program_database_page.py`.
- `project_data_editor_page.py` — CRUD for the Project/Repo registry
  (`core/store.py`'s `MetadataStore`). **Add** Repo still uses the full
  `interface/shared/dialogs.py`'s `RepoDialog` (name/URL/thumbnail/
  requirements — the one-step bootstrap for a brand-new repo record); the
  **Edit** flow here now only asks for Name/Git URL
  (`RepoDialog(show_thumbnail=False)`) — Thumbnail and Requirements/Add-ons
  editing for an *existing* repo moved to `interface/about/repo_about_page.py`.
  `CATEGORY_DEVELOPER`.
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

**Removed:** `addon_settings_page.py`/`AddonSettingsPage` (the "Add-ons"
tab) — deprecated and removed as of 2026-07-14. It used to be the only UI
for editing a discovered add-on's icon/description override/required
Program(s) (`core/addon_store.py`'s `AddonMetadataStore`); no replacement
UI exists yet, see `add-on/README.md`'s "Icon, description override, and
required Program" section.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `shared/` addition, or touches `main_window.py`'s
wiring (which shows/hides this view via `Sidebar.settings_requested`).
