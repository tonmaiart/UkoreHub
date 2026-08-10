# plugins/core/explorer/

The Explorer tab (`SectionRegistry` key `repo_browser`) — browse a cloned
repo's files, with a Miller-column Folder Navigator and a per-path commit
history panel. A real always-on `plugins/core/` plugin (see
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
  reaches into `page.browser.commit_panel._worker`. (Used to also register
  an `ExplorerSettingsPage`/"Add Pinned Repo..." `CATEGORY_REPO` Settings
  tab and a `pinned_repo_browser_page.py` dynamic-tab page — the whole
  pinned-repo feature was removed as no longer needed; see git history if
  it needs to come back.)
- `repo_browser_page.py` — `RepoBrowserPage`: the top-level Explorer page.
  Owns file-open delegation (`core/extensibility/file_opener.py`'s
  `FileOpenerRegistry`, so a plugin can claim an extension) and implements
  the optional `browse_to_path(path)` protocol method (see
  `interface/section_registry.py`'s `UICommandService`) — `plugins/core/submit/`
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
  Setting button). `add_folder_button` sits right after `up_button` in the
  nav row (icon `add_folder.png`, also at the repo root, same fallback
  convention) and just calls `_create_new_folder(self._current_path)` — a
  toolbar shortcut for the same "Create New Folder" action described below.
  Right-clicking a row opens a context menu (Copy Name/Copy
  File Path/Rename/Delete) via `_on_table_context_menu`; right-clicking
  blank space in the table (no row under the cursor) falls through to
  `_on_empty_area_context_menu` instead, whose Create New
  Folder/Rename Folder/Delete Folder act on the currently open folder
  (`_current_path`) rather than a selected row — Rename/Delete Folder are
  disabled while `_current_path` is the repo root, since renaming/deleting
  it out from under `set_root()`'s `fs_model`/`_last_opened_store` would
  leave them pointed at a path that no longer exists. The file table hides
  the Type column (redundant with
  the file's icon/name) and gives Name/Date Modified `Stretch` resize
  priority over Size so they can't get squeezed narrow. `search_edit`
  (width-capped) sits at the end of the same row as the breadcrumb path
  field rather than on its own row below the table. Each Folder Navigator
  column list uses zero item padding/margin (on top of `setSpacing(0)`) to
  keep entries as compact as possible. A "Last Opened Files" `QGroupBox`
  (`last_opened_list`) sits at the far right of the Folder Navigator row —
  an MRU list (capped at `_MAX_LAST_OPENED`) appended to whenever a table
  double-click actually opens a file (`_record_last_opened`, called from
  `_on_table_double_clicked`), backed by `LastOpenedStore`
  (`last_opened_store.py`, see below) rather than kept purely in-memory —
  rebuilt from that store on every `set_root()`/repo switch, so it
  survives app restarts. Clicking an entry (`_on_last_opened_clicked`)
  navigates to that file's current parent folder and then selects the
  file's own row in the table (`_select_file_in_table`, via
  `fs_model.index()`/`proxy.mapFromSource()`) — deliberately no
  double-click-to-open wired up here, so this list can never be a second
  way to launch a file, only a navigation-plus-highlight shortcut back to
  one. `open_directory_button` ("Open Directory") sits on its own row below
  the file table — opens `_current_path` in the OS file explorer via
  `core/os_utils.py`'s `open_in_file_explorer`. Kept out of `nav_row`
  deliberately: it hands off to the OS rather than navigating within the
  app, unlike every other nav_row button.
- `last_opened_store.py` — `LastOpenedStore`: persists the Last Opened
  Files list to **this app's own**
  `<UkoreHub_root>/cache/explorer/last_opened_<repo_id>_<username>.json`
  — a **local, per-repo, per-OS-user** cache, not team/studio-shared data
  (never goes through `PluginConfigStore`/`api.plugin_config_store`).
  Stores repo-relative paths (survives a different drive letter machine to
  machine), scoped by both the repo's id and OS username (`getpass.getuser()`,
  sanitized to a safe filename). Used to live at
  `<browsed_repo_root>/.ukorehub/explorer_last_opened_<username>.json`
  instead (same convention as UkoreBrowser's (now its own `cache/plugins/`
  clone)
  `maya-scripts/UkoreBrowser/core/browser_config.py`'s
  `BrowserConfig`) but that put the file inside whatever production repo was
  being browsed, at the mercy of *that* repo's own `.gitignore` — several
  studio repos didn't exclude `.ukorehub/`, so this list kept getting
  committed to their history. `cache/` is this app's own repo, already
  wholesale gitignored (`/cache/` in this app's `.gitignore`, same directory
  `cache/plugins/` repo plugins live under), so this sidesteps the problem
  entirely rather than depending on every browsed repo's `.gitignore` being
  correct. `get_last_opened()` also prunes (and persists the removal of) any
  entry whose file no longer exists on disk, so deleted files don't linger
  in the list forever.
- `path_commit_history_panel.py` — `PathCommitHistoryPanel`: commit
  history scoped to whichever path is currently being viewed — narrower
  than the whole-repo log on `plugins/core/submit/repo_git_status_page.py`.
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
`interface/main_window.py`'s generic `UICommandService` wiring.
