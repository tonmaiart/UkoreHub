# interface/shared/

Widgets/helpers genuinely used by 2+ of the window-scoped folders above —
kept visible here rather than force-fit into whichever folder happened to
use it first, so no window folder quietly depends on a "foreign" one.
Every file here has a confirmed multi-window consumer (checked repo-wide
before the `interface/` reorg that created this folder, and re-checked
whenever a domain folder is split out — `dialogs.py` moved out 2026-07-20
once a repo-wide grep showed `ProjectDialog`/`RepoDialog`/
`RequirementsTreeWidget` had only one real consumer left,
`plugins/core/project_editor/`, which now owns `ProjectDialog`/`RepoDialog`
directly as `project_editor/dialogs.py` — `RequirementsTreeWidget` moved
back out to this folder on its own 2026-08-04 once
`interface/repo_settings/requirements_and_plugins_page.py` became a second
real consumer) — if a file only ever gets one consumer, it belongs in that
consumer's own folder instead, not here.

- `base_repo_settings_page.py` — `BaseRepoSettingsPage`: shared base for a
  Settings tab scoped to a single repo — the `empty_label`/`content_widget`
  scaffolding and `refresh()` preamble (resolve active project/repo from
  `local_config_store`, catch `NotFoundError`, `show_exclusive`) that
  `interface/repo_settings/local_repository_page.py`,
  `interface/repo_settings/requirements_and_plugins_page.py`, and
  `interface/browser_links/browser_links_settings_page.py` each had
  independently, byte-for-byte identical, before 2026-07-20. A subclass
  adds its own layout onto `content_widget` (left layout-less on purpose —
  `BrowserLinksSettingsPage` wraps it in a scroll area, the other two
  don't) and overrides `_on_refresh_content()`.
- `requirements_tree_widget.py` — `RequirementsTreeWidget`: each Program is
  a checkable top-level node (check = required), with a checkable child per
  version for a multi-version Program (pin, radio-style). Used by
  `plugins/core/project_editor/dialogs.py`'s `RepoDialog` (repo creation)
  and `interface/repo_settings/requirements_and_plugins_page.py` (editing
  an existing repo's requirements).
- `commit_history.py` — `CommitCard` widget, `CommitHistoryEntry`,
  `format_commit_date`, and `fetch_entries_via_github` (GitHub-API-first,
  local-git-fallback). Used by `plugins/core/explorer/`'s per-path commit
  panel (`path_commit_history_panel.py`/`path_commit_history_worker.py`)
  and `plugins/core/Notification/`'s team activity feed
  (`commit_feed_worker.py`, via `fetch_entries_via_github` only — it
  doesn't use `CommitCard` itself, see that plugin's README). Submit used
  to render a whole-repo commit log through this module too
  (`repo_git_status_page.py`/`commit_log_worker.py`) but that's been
  removed now that Notification's feed covers it — see
  `plugins/core/submit/README.md`. Stays in `interface/shared/` rather than
  moving into either plugin since it's imported the same normal way from
  more than one `plugins/core/` plugin.
- `image_asset.py` — `pick_image_file` (the `QFileDialog.getOpenFileName`
  wrapper every icon/thumbnail chooser uses) and `save_image_asset` (copy
  the chosen file into a `data/*_icons`/`data/thumbnails`-style dir as
  `f"{asset_id}{ext}"`, returning the filename or `None` + a warning on
  failure). Used by `plugins/core/project_editor/`'s node context menu
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
