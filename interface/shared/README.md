# interface/shared/

Widgets/helpers genuinely used by 2+ of the window-scoped folders above —
kept visible here rather than force-fit into whichever folder happened to
use it first, so no window folder quietly depends on a "foreign" one.
Every file here has a confirmed multi-window consumer (checked repo-wide
before the `interface/` reorg that created this folder, and re-checked
whenever a domain folder is split out — `dialogs.py` moved out 2026-07-20
once a repo-wide grep showed `ProjectDialog`/`RepoDialog`/
`RequirementsTreeWidget` had only one real consumer left,
`plugins/studio/project_editor/`, which now owns that file directly as
`project_editor/dialogs.py`) — if a file only ever gets one consumer, it
belongs in that consumer's own folder instead, not here.

- `base_repo_settings_page.py` — `BaseRepoSettingsPage`: shared base for a
  Settings tab scoped to a single repo — the `empty_label`/`content_widget`
  scaffolding and `refresh()` preamble (resolve active project/repo from
  `local_config_store`, catch `NotFoundError`, `show_exclusive`) that
  `interface/repo_settings/local_repository_page.py`,
  `interface/repo_settings/enable_plugin_page.py`, and
  `interface/browser_links/browser_links_settings_page.py` each had
  independently, byte-for-byte identical, before 2026-07-20. A subclass
  adds its own layout onto `content_widget` (left layout-less on purpose —
  `BrowserLinksSettingsPage` wraps it in a scroll area, the other two
  don't) and overrides `_on_refresh_content()`.
- `commit_history.py` — `CommitCard` widget, `CommitHistoryEntry`,
  `format_commit_date`, and `fetch_entries_via_github` (GitHub-API-first,
  local-git-fallback). Used by `plugins/studio/explorer/`'s per-path commit
  panel (`path_commit_history_panel.py`/`path_commit_history_worker.py`)
  and `plugins/studio/submit/`'s whole-repo commit log
  (`repo_git_status_page.py`/`commit_log_worker.py`), so both render
  identically — Explorer and Submit are real `plugins/studio/` plugins now
  (not `interface/` window folders), but this stays in `interface/shared/`
  since it's imported the same normal way either side of that split.
- `image_asset.py` — `pick_image_file` (the `QFileDialog.getOpenFileName`
  wrapper every icon/thumbnail chooser uses) and `save_image_asset` (copy
  the chosen file into a `data/*_icons`/`data/thumbnails`-style dir as
  `f"{asset_id}{ext}"`, returning the filename or `None` + a warning on
  failure). Used by `plugins/studio/project_editor/`'s node context menu
  (repo thumbnail and `RepoDialog`), `browser_links/browser_links_settings_page.py`
  (Browser Link icon), and `settings/program_dialog.py`/
  `settings/program_database_page.py` — every place in the app that lets
  you pick and persist an image asset.
- `widget_helpers.py` — three small Qt boilerplate extractions used across
  multiple windows: `wrap_scrollable` (the `QScrollArea(widgetResizable)`
  wrapper every scrollable tab/panel builds by hand), `confirm_action` (the
  Yes/No-defaulting-to-No `QMessageBox.warning` every delete/revert
  confirmation uses), and `show_exclusive` (the empty-state/content-state
  visibility toggle every page's `set_repo()` does).

**Working here:** a change to a file in this folder affects every window
listed above for it — check all of them, not just the one that sent you
here.
