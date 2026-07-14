# interface/settings/

The "Setting" view — shown via the icon-only Setting button in Sidebar's
footer (app-level, not one of the repo-scoped `SectionTabList` rows). Every
page here **self-persists on every change** — there is no Save/Cancel step
anywhere; `SettingsTabSpec` has no `on_save`/`on_cancel` hooks.

- `settings_view.py` — `SettingsView`: the left-tab-bar shell, driven by
  `interface/settings_tab_registry.py`'s `SettingsTabRegistry` (open,
  ordered — built-in and plugin-provided tabs register into the same
  collection, see `interface/builtin_settings_tabs.py`). `get_tab_widget(key)`
  is the one public escape hatch for reaching a specific constructed page
  from outside — `main_window.py` uses it to connect
  `CommonSettingsPage.logout_requested` without this view needing to know
  what that page is.
- `common_settings_page.py` — workspace folder, theme (unpickable in the
  UI today, see `core/theme.py`), GitHub OAuth Client ID, and the Logout
  button (moved here from Sidebar's footer — `logout_requested` signal,
  connected in `main_window.py` to the same logout flow the old toggle
  button used to trigger).
- `program_database_page.py` — CRUD for the shared Program Database
  (`core/program_store.py`), using `program_dialog.py`'s `ProgramDialog`
  for add/edit.
- `program_dialog.py` — `ProgramDialog`: name/version/description/icon
  editor for one `Program`, used only by `program_database_page.py`.
- `project_data_editor_page.py` — CRUD for the Project/Repo registry
  (`core/store.py`'s `MetadataStore`). **Add** Repo still uses the full
  `interface/shared/dialogs.py`'s `RepoDialog` (name/URL/thumbnail/
  requirements — the one-step bootstrap for a brand-new repo record); the
  **Edit** flow here now only asks for Name/Git URL
  (`RepoDialog(show_thumbnail=False)`) — Thumbnail and Requirements/Add-ons
  editing for an *existing* repo moved to `interface/about/repo_about_page.py`.
- `project_status_page.py` — read-only per-repo clone/sync status tree.
- `plugin_catalog_page.py` — read-only listing of what got discovered
  under `plugins/`.
- `addon_settings_page.py` — studio-editable overrides for a discovered
  add-on (icon, description, required Program), using
  `interface/shared/dialogs.py`'s `AddonSettingsDialog`.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `shared/` addition, or touches `main_window.py`'s
wiring (which shows/hides this view via `Sidebar.settings_requested`).
