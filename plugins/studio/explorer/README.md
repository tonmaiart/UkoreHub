# plugins/studio/explorer/

The Explorer tab (`SectionRegistry` key `repo_browser`) — browse a cloned
repo's files, with a Miller-column Folder Navigator and a per-path commit
history panel. A real always-on `plugins/studio/` plugin (see
`core/extensibility/README.md` for the plugins-vs-add-ons distinction and
`core/extensibility/loader.py` for how `manifest.json`/`plugin.py` are
discovered/loaded) — not special-cased by `interface/`, registers into
`SectionRegistry` the same way any other plugin would. (Recent Files and
Favorites used to live in a left sidebar here — removed for a cleaner
Explorer; the Up/Back nav buttons at the top of the file table are the only
navigation aids now.)

- `manifest.json` — plugin id `explorer`, entry point `plugin.py`.
- `plugin.py` — `register(api)`: constructs `RepoBrowserPage` from
  `api.local_config`/`api.git`/`api.file_opener_registry`, registers it as
  the `SectionSpec(key="repo_browser", order=10, ...)` section. Also wires
  `background_threads` (for `MainWindow.closeEvent`'s shutdown cleanup) —
  reaches into `page.browser.commit_panel._worker`. Additionally registers
  `explorer_settings_page.py`'s `ExplorerSettingsPage` as a
  `CATEGORY_REPO` Settings tab (`key="explorer_settings"`, a convention-only
  string match `interface/main_window.py` reaches into via
  `SettingsView.get_tab_widget()` to wire its `pins_changed` signal — see
  below).
- `explorer_settings_page.py` — `ExplorerSettingsPage`: per-repo list of
  other repos "pinned" as extra Explorer-style sidebar tabs while this repo
  is active (`Repo.explorer_pins`, `core/models.py`'s `ExplorerPin` —
  `target_project_id`/`target_repo_id`/`label`). Same self-resolving-
  active-repo `refresh()` pattern as
  `interface/settings/browser_links_settings_page.py`. "Add Pinned
  Repo..." reuses `interface/login/repo_picker.py`'s `RepoPickerDialog`
  (the same dialog `MainWindow._on_select_repo` already uses) but narrows
  it via that dialog's `allowed_pairs` filter to only the active repo's
  declared pipeline inputs/outputs — read from
  `plugins/studio/pipeline_architect`'s `PluginConfigStore` (constructed
  with that plugin's id string, `pipeline_config_store` param, per the
  "convention, not import" cross-plugin data pattern — see that plugin's
  README) rather than the whole registry. `_pipeline_repo_pairs()` calls
  `.load()` on that store before reading, since it's a separate
  `PluginConfigStore` object from pipeline_architect's own and would
  otherwise only see whatever was on disk at app startup. If the active
  repo has no pipeline inputs/outputs declared yet, the button shows a
  message pointing at Project Data Editor instead of opening an empty
  picker. Every change self-persists via `MetadataStore.set_repo_explorer_pins`
  and emits `pins_changed`, which `interface/main_window.py` connects to
  `_rebuild_dynamic_tabs`.
- `pinned_repo_browser_page.py` — `PinnedRepoBrowserPage`: one dynamically-
  created top-level tab per `ExplorerPin`, bound at construction to a FIXED
  target repo (never the app's active repo — implements `set_repo()` as a
  no-op, same convention `interface/about/browser_link_page.py`'s
  `BrowserLinkPage` uses for MainWindow's other class of dynamic tab). Reuses
  the same `RepoBrowserWidget` the main Explorer tab uses once the target is
  cloned; shows a "Clone" button + a live streamed log (backed by a small
  `_CloneWorker(QThread)` around `GitService.clone`, same shape as
  `path_commit_history_worker.py`'s worker) when it isn't. Exposes
  `background_threads()` (clone worker + `browser.commit_panel._worker`) so
  `interface/main_window.py`'s `_rebuild_dynamic_tabs`/`closeEvent` can stop
  them safely — this page owns real `QThread`s, unlike `BrowserLinkPage`.
  **Constructed directly by `interface/main_window.py`** (a deliberate,
  documented exception to "MainWindow doesn't import plugin-specific
  types" — see the comment at that import) since it needs the exact same
  dynamic-tab machinery Browser Link tabs already use there.
- `repo_browser_page.py` — `RepoBrowserPage`: the top-level Explorer page.
  Owns file-open delegation (`core/extensibility/file_opener.py`'s
  `FileOpenerRegistry`, so an add-on can claim an extension) and implements
  the optional `browse_to_path(path)` protocol method (see
  `interface/section_registry.py`'s `SectionHost`) — `plugins/studio/submit/`
  calls into this generically via `MainWindow`'s `navigate_and_focus`, not by
  importing this module directly.
- `browser_widget.py` — `RepoBrowserWidget`: the actual browser — a
  Miller-column "Folder Navigator", a sortable/searchable file table with
  Up/Back navigation, and the per-path commit history panel docked to the
  right of the table. `history_back_button` returns to whatever path was
  current before the last navigation (`_back_stack`); `up_button` always
  jumps to the current path's parent regardless of history — different
  semantics, so don't conflate them. Both use icons (`icons8-back-50.png` /
  `icons8-up-50.png`, both at the repo root) with a text fallback if the
  file isn't there (same pattern as `interface/sidebar/sidebar.py`'s
  Setting button). The file table hides the Type column (redundant with
  the file's icon/name) and gives Name/Date Modified `Stretch` resize
  priority over Size so they can't get squeezed narrow. `search_edit`
  (width-capped) sits at the end of the same row as the breadcrumb path
  field rather than on its own row below the table. Each Folder Navigator
  column list uses zero item padding/margin (on top of `setSpacing(0)`) to
  keep entries as compact as possible.
- `path_commit_history_panel.py` — `PathCommitHistoryPanel`: commit
  history scoped to whichever path is currently being viewed — narrower
  than the whole-repo log on `plugins/studio/submit/repo_git_status_page.py`.
  Shares `CommitCard`/`CommitHistoryEntry` with Submit via
  `interface/shared/commit_history.py` (that shared helper module stays in
  `interface/`, imported normally by both plugins).
- `file_table_proxy.py` — `FileTableFilterProxy`: the `QSortFilterProxyModel`
  behind the file table (search-text filtering).
- `path_commit_history_worker.py` — `QThread` backing
  `path_commit_history_panel.py`'s GitHub-API-first/local-git-fallback
  fetch, off the UI thread.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `interface/shared/` addition, or touches
`interface/main_window.py`'s generic `SectionHost` wiring or its
`_rebuild_dynamic_tabs`/`closeEvent` (pinned-tab construction/cleanup).
