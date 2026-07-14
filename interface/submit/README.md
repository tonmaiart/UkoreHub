# interface/submit/

The Submit tab (`SectionRegistry` key `repo_git_status`) — stage/unstage/
revert, commit → pull → (resolve conflicts) → push, and the whole-repo
commit log.

- `repo_git_status_page.py` — `RepoGitStatusPage`: the top-level Submit
  page registered into `SectionRegistry` (see
  `interface/builtin_sections.py`). Drives the full sync/commit/pull/push
  workflow via the workers below, shows Modified/Staged lists, and renders
  the whole-repo commit log (paginated, "Load More").
- `commit_dialog.py` — `CommitDialog`: commit message entry (+ amend
  checkbox), shown before the pull→push workflow starts.
- `conflict_dialog.py` — `ConflictResolutionDialog`: per-file keep-ours/
  keep-theirs resolution, shown when a pull hits a merge conflict.
- `log_panel.py` — `LogPanel`: scrolling read-only log output during
  sync/push/pull.
- `git_stream_worker.py` — `GitStreamWorker`: generic `QThread` that
  streams a git command's output line-by-line and emits whatever it
  returns via `finished_ok`. Used for the Sync button's `open_or_sync`
  (clone/pull, also driving `MainWindow._start_auto_sync`'s launch/
  repo-switch auto-sync) as well as the pull and push steps of the commit
  workflow — one generic worker where there used to be a separate
  `GitWorker` class just for `open_or_sync`.
- `status_worker.py` — `RepoStatusWorker`: fetches working-tree status
  (modified/staged/untracked) off the UI thread.
- `commit_log_worker.py` — `CommitLogWorker`: fetches a page of the
  whole-repo commit log (GitHub-API-first, local-git-fallback) off the UI
  thread; shares `CommitCard`/`CommitHistoryEntry` with Explorer via
  `interface/shared/commit_history.py`.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `shared/` addition, or touches `main_window.py`'s
wiring (which registers this page into `SectionRegistry` and connects its
`sync_started`/`sync_finished`/`sync_failed`/`browse_file_requested`
signals).
