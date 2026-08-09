# interface/browser_links/

The Browser Link feature, end-to-end — configuring `Repo.browser_links`
and surfacing them as dynamic Sidebar rows. As of this refactor there's no
embedded browser anywhere in the app: clicking a Browser Link row opens
its URL in the OS's default browser (`QDesktopServices.openUrl`) instead
of an in-app `QWebEngineView` tab — removed along with the rest of
QtWebEngine (the shared `QWebEngineProfile`/cookie-persistence machinery,
`web_engine_profile.py`, and the tab widget itself, `browser_link_page.py`,
are both gone) so the app no longer carries a Chromium subsystem dependency
at all.

- `browser_links_settings_page.py` — `BrowserLinksSettingsPage`:
  add/rename/remove/change-icon for the active repo's Browser Links
  (`core/models.py`'s `BrowserLink`, `icon_filename` falls back to
  `assets/icons/icons8-browser-50.png`). A `CATEGORY_REPO` Settings tab
  (registered in `interface/builtin_settings_tabs.py`), rendered inside
  `interface/settings/settings_view.py`'s Repo Setting (Dev) top tab like
  every other `CATEGORY_REPO` tab. Unlike most `CATEGORY_REPO` tabs it's
  genuinely scoped to a single repo, so it can't rely on `set_repo()`
  (`MainWindow` never calls that on Settings pages) — it subclasses
  `interface/shared/base_repo_settings_page.py`'s `BaseRepoSettingsPage`,
  which resolves the active project/repo itself from `local_config_store`
  on `refresh()` (called on construction and on `on_activated`) and calls
  `_on_refresh_content()` for the rebuild.

**Runtime rendering:** `interface/main_window.py`'s `_rebuild_dynamic_tabs`
rebuilds one `SectionTabList` row per configured Browser Link on every
repo switch and whenever `browser_links_changed` fires — not a
`SectionRegistry` section, and (as of this refactor) not a `view_stack`
page either. `SectionTabList.add_dynamic_tab(key, label, icon_path, url=...)`
registers the row's target URL; clicking it emits
`external_link_activated(url)` instead of the usual `navigation_changed(key)`
(see that file's class docstring), which `Sidebar` forwards up to
`MainWindow._on_external_link_activated` — `QDesktopServices.openUrl(QUrl(url))`,
nothing else. The row never becomes the "current" selected row (clicking
it snaps selection back to whatever page was actually showing), since
there's no page for it to show.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive or touches `main_window.py`'s wiring (which rebuilds the
dynamic Browser Link rows on every repo switch and connects
`Sidebar.external_link_activated`).
