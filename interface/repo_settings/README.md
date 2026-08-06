# interface/repo_settings/

The repo-configuration domain — Settings tabs that manage one specific
per-repo concern, as opposed to `interface/settings/`'s app/machine-level
tabs (Program Database, GitHub OAuth Client ID, Plugins catalog). Split out
so a change to one of these doesn't sit in the same folder as unrelated
app-level settings just because both happen to register into
`SettingsTabRegistry`.

Both tabs are `CATEGORY_REPO` (registered in
`interface/builtin_settings_tabs.py`) and — like every `CATEGORY_REPO`
tab — are not rendered by `interface/settings/settings_view.py` at all;
they show up in `plugins/core/project_editor/`'s "Repository Setting"
popup instead, read generically off `SettingsTabRegistry` (see
`interface/settings/README.md`'s "No longer rendered here at all" note).
Both are genuinely scoped to a single repo, so neither relies on
`set_repo()` (`MainWindow` never calls that on Settings pages) — both
subclass `interface/shared/base_repo_settings_page.py`'s
`BaseRepoSettingsPage`, which resolves the active project/repo itself from
`local_config_store` on `refresh()` (called on construction and on
`on_activated`) and calls each page's own `_on_refresh_content()` override
for the type-specific rebuild.

- `local_repository_page.py` — `LocalRepositoryPage`: shows the active
  repo's local clone status/path and a "Remove Local Repositories" button
  that `shutil.rmtree`s the clone folder (`core/paths.py`'s
  `resolve_repo_path`) and marks the repo `not_cloned`
  (`MetadataStore.mark_status`) — does not touch the Project/Repo registry
  record itself, only the on-disk clone.
- `requirements_and_plugins_page.py` — `RequirementsAndPluginsPage`: the
  "Requirements & Plugins" tab (2026-08-04, merging what used to be two
  separate `CATEGORY_REPO` tabs — Requirements, formerly owned by
  `plugins/core/project_editor/`, and this folder's own Enable Plugin).
  Two stacked sections inside a `wrap_scrollable()` scroll area
  (2026-08-05, so the tree plus three plugin lists don't cram into
  whatever height the "Repository Setting..." popup has): Program
  Requirements (embeds
  `interface/shared/requirements_tree_widget.py`'s `RequirementsTreeWidget`
  — the same checkable Program tree `RepoDialog` shows at Add-Repo time,
  here editing an *existing* repo's `required_program_ids`/
  `program_version_pins`), and Enable Plugin — every discovered plugin,
  split into three lists by `core.extensibility.loader.plugin_source()`
  instead of one flat checklist, laid out as three columns in one row:
  **Core** (`plugins/core/`) — always on,
  no checkbox, no per-repo opt-out at all; **Internal**
  (`plugins/repo_internal/`) and **External** (`cache/plugins/`) — both
  opt-in, unchecked by default, both persisted to the same
  `Repo.required_plugin_ids` list. (Un)checking an Internal/External
  plugin actually flips its sidebar section's visibility for this repo
  (enforced in `interface/main_window.py`'s `_apply_plugin_visibility`,
  wired via a plugin-id-to-section-key map built in `launcher.py`).

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `shared/` addition, or touches
`plugins/core/project_editor/repo_settings_panel.py` (the actual
container that renders these tabs) or `interface/main_window.py`'s
`_apply_plugin_visibility`.
