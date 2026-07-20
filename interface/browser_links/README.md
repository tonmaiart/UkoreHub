# interface/browser_links/

The Browser Link feature, end-to-end — configuring `Repo.browser_links`
and rendering them as tabs, previously split across `interface/settings/`
(the settings/CRUD half) and `interface/about/` (the runtime/display half,
after "About" itself was removed 2026-07-20) purely because they were
grouped by "kind of UI" rather than by feature. Colocated here instead so
a change to Browser Links only ever touches this one folder.

- `browser_links_settings_page.py` — `BrowserLinksSettingsPage`:
  add/rename/remove/change-icon for the active repo's Browser Links
  (`core/models.py`'s `BrowserLink`, `icon_filename` falls back to
  `data/icons/icons8-browser-50.png`). A `CATEGORY_REPO` Settings tab
  (registered in `interface/builtin_settings_tabs.py`), rendered inside
  `plugins/studio/project_editor/`'s "Repository Setting" popup like every
  other `CATEGORY_REPO` tab — see `interface/settings/README.md`'s "No
  longer rendered here at all" note. Unlike most `CATEGORY_REPO` tabs it's
  genuinely scoped to a single repo, so it can't rely on `set_repo()`
  (`MainWindow` never calls that on Settings pages) — it subclasses
  `interface/shared/base_repo_settings_page.py`'s `BaseRepoSettingsPage`,
  which resolves the active project/repo itself from `local_config_store`
  on `refresh()` (called on construction and on `on_activated`) and calls
  `_on_refresh_content()` for the rebuild.
- `browser_link_page.py` — `BrowserLinkPage`: one dynamically-created
  top-level tab per configured Browser Link (not a `SectionRegistry`
  section — rebuilt on every repo switch by `interface/main_window.py`'s
  `_rebuild_dynamic_tabs`). Embeds the link's URL in a `QWebEngineView`
  behind a Back/Forward/Reset toolbar, using the shared persistent
  `QWebEngineProfile` from `web_engine_profile.py`.
- `web_engine_profile.py` — `make_persistent_browser_link_profile`: the
  single disk-backed `QWebEngineProfile` `main_window.py` constructs once
  (in its own `__init__`) and passes to every `BrowserLinkPage` it builds,
  so a login (Notion, Google Sheet, ...) survives app restarts instead of
  being cleared every session. Single-consumer (`browser_link_page.py`)
  — kept as its own file rather than folded into that one since it's
  constructed once by `main_window.py` and threaded through, not
  instantiated by the page itself.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive or touches `main_window.py`'s wiring (which constructs
the shared `QWebEngineProfile` and rebuilds the dynamic Browser Link tabs
on every repo switch).
