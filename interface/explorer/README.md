# interface/explorer/

The Explorer tab (`SectionRegistry` key `repo_browser`) — browse a cloned
repo's files, with a Miller-column Folder Navigator and a per-path commit
history panel. (Recent Files and Favorites used to live in a left sidebar
here — removed for a cleaner Explorer; the Up/Back nav buttons at the top
of the file table are the only navigation aids now.)

- `repo_browser_page.py` — `RepoBrowserPage`: the top-level Explorer page
  registered into `SectionRegistry` (see `interface/builtin_sections.py`).
  Owns file-open delegation (`core/extensibility/file_opener.py`'s
  `FileOpenerRegistry`, so an add-on can claim an extension).
- `browser_widget.py` — `RepoBrowserWidget`: the actual browser — a
  Miller-column "Folder Navigator", a sortable/searchable file table with
  Up/Back navigation, and the per-path commit history panel docked to the
  right of the table. `history_back_button` returns to whatever path was
  current before the last navigation (`_back_stack`); `up_button` always
  jumps to the current path's parent regardless of history — different
  semantics, so don't conflate them. Both use icons
  (`data/icons/icons8-back-50.png` / `icons8-up-50.png`) with a text
  fallback if the file isn't there (same pattern as `sidebar.py`'s Setting
  button) — as of this writing those two icon files don't exist yet.
- `path_commit_history_panel.py` — `PathCommitHistoryPanel`: commit
  history scoped to whichever path is currently being viewed — narrower
  than the whole-repo log on `interface/submit/repo_git_status_page.py`.
  Shares `CommitCard`/`CommitHistoryEntry` with Submit via
  `interface/shared/commit_history.py`.
- `file_table_proxy.py` — `FileTableFilterProxy`: the `QSortFilterProxyModel`
  behind the file table (search-text filtering).
- `path_commit_history_worker.py` — `QThread` backing
  `path_commit_history_panel.py`'s GitHub-API-first/local-git-fallback
  fetch, off the UI thread.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `shared/` addition, or touches `main_window.py`'s
wiring (which registers this page into `SectionRegistry`).
