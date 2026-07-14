# interface/shared/

Widgets/helpers genuinely used by 2+ of the window-scoped folders above —
kept visible here rather than force-fit into whichever folder happened to
use it first, so no window folder quietly depends on a "foreign" one.
Every file here has a confirmed multi-window consumer (checked repo-wide
before the `interface/` reorg that created this folder) — if a file only
ever gets one consumer, it belongs in that consumer's own folder instead,
not here.

- `commit_history.py` — `CommitCard` widget, `CommitHistoryEntry`,
  `format_commit_date`, and `fetch_entries_via_github` (GitHub-API-first,
  local-git-fallback). Used by `plugins/studio/explorer/`'s per-path commit
  panel (`path_commit_history_panel.py`/`path_commit_history_worker.py`)
  and `plugins/studio/submit/`'s whole-repo commit log
  (`repo_git_status_page.py`/`commit_log_worker.py`), so both render
  identically — Explorer and Submit are real `plugins/studio/` plugins now
  (not `interface/` window folders), but this stays in `interface/shared/`
  since it's imported the same normal way either side of that split.
- `dialogs.py` — `ProjectDialog`/`RepoDialog` (used by
  `interface/settings/project_data_editor_page.py`),
  `RequirementsTreeWidget` (the checkable Program/Add-on tree shape,
  shared internally by the two dialogs below), and
  `RequirementsEditDialog` (used by
  `interface/about/repo_about_page.py`'s Requirement sub-tab).
- `project_repo_tree.py` — `populate_project_tree` and the
  `PROJECT_ROLE`/`REPO_ROLE` item-data roles behind the Project/Repo
  `QTreeWidget` shape. Used by `interface/settings/project_data_editor_page.py`
  + `project_status_page.py` (admin/status views — full columns, editable or
  read-only). `interface/login/repo_picker.py`'s `RepoPickerDialog` used to
  be a third consumer but is card-based now (name + status only, nothing
  else), not a tree, so it no longer imports this file.
- `image_asset.py` — `pick_image_file` (the `QFileDialog.getOpenFileName`
  wrapper every icon/thumbnail chooser uses) and `save_image_asset` (copy
  the chosen file into a `data/*_icons`/`data/thumbnails`-style dir as
  `f"{asset_id}{ext}"`, returning the filename or `None` + a warning on
  failure). Used by `about/repo_about_page.py` (repo thumbnail),
  `settings/project_data_editor_page.py`, `settings/browser_links_settings_page.py`
  (Browser Link icon), `program_dialog.py`, `program_database_page.py`, and
  `shared/dialogs.py`'s `RepoDialog` — every place in the app that lets you
  pick and persist an image asset.
- `widget_helpers.py` — three small Qt boilerplate extractions used across
  multiple windows: `wrap_scrollable` (the `QScrollArea(widgetResizable)`
  wrapper every scrollable tab/panel builds by hand), `confirm_action` (the
  Yes/No-defaulting-to-No `QMessageBox.warning` every delete/revert
  confirmation uses), and `show_exclusive` (the empty-state/content-state
  visibility toggle every page's `set_repo()` does).

**Working here:** a change to a file in this folder affects every window
listed above for it — check all of them, not just the one that sent you
here.
