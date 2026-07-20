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
they show up in `plugins/studio/project_editor/`'s "Repository Setting"
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
- `enable_plugin_page.py` — `EnablePluginPage`: per-repo checkbox list over
  every discovered `plugins/studio`+`plugins/local` entry
  (`Repo.active_plugin_ids`). **Distinct from Add-ons**
  (`Repo.enabled_addon_ids`) — see `core/README.md`'s note on the
  difference; unlike Add-ons, unchecking a plugin here actually hides its
  sidebar section for this repo (enforced in
  `interface/main_window.py`'s `_apply_plugin_visibility`, wired via a
  plugin-id-to-section-key map built in `launcher.py`). An empty
  `active_plugin_ids` (the default) means "unrestricted" — every plugin
  stays visible. A plugin flagged `manifest.json` `"core": true`
  (`PluginManifest.core`, e.g. `plugins/studio/project_editor/`) renders
  here checked and disabled — it can never actually be hidden, so there's
  nothing to toggle.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `shared/` addition, or touches
`plugins/studio/project_editor/repo_settings_panel.py` (the actual
container that renders these tabs) or `interface/main_window.py`'s
`_apply_plugin_visibility`.
