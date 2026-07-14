# plugins/studio/submit/

The Submit tab (`SectionRegistry` key `repo_git_status`) — stage/unstage/
revert, commit → pull → (resolve conflicts) → push, and the whole-repo
commit log. A real always-on `plugins/studio/` plugin (see
`core/extensibility/README.md` for the plugins-vs-add-ons distinction and
`core/extensibility/loader.py` for how `manifest.json`/`plugin.py` are
discovered/loaded) — not special-cased by `interface/`, registers into
`SectionRegistry` the same way any other plugin would.

- `manifest.json` — plugin id `submit`, entry point `plugin.py`.
- `plugin.py` — `register(api)`: constructs `RepoGitStatusPage` from
  `api.metadata`/`api.local_config`/`api.git`, registers it as the
  `SectionSpec(key="repo_git_status", order=20, ...)` section. Also wires
  `background_threads` (reaches into `page._git_worker`/`_status_worker`/
  `_stream_worker`/`_commit_log_worker` for `MainWindow.closeEvent`'s
  shutdown cleanup) and `wire` — connects `sync_started`/`sync_finished`/
  `sync_failed` to `SectionHost.set_status_message` (the sidebar status
  line) and `browse_file_requested` to `SectionHost.navigate_and_focus`
  (jumps to Explorer's `"repo_browser"` section key and calls its optional
  `browse_to_path` protocol method — see
  `plugins/studio/explorer/repo_browser_page.py`). See
  `interface/section_registry.py`'s `SectionHost` for why this is a fixed
  set of named callbacks rather than a generic dispatcher.
- `repo_git_status_page.py` — `RepoGitStatusPage`: the top-level Submit
  page. Drives the full sync/commit/pull/push workflow via the workers
  below, shows Modified/Staged lists, and renders the whole-repo commit log
  (paginated, "Load More"). The Sync/Refresh Status buttons live under the
  log panel inside a "Git Log" `QGroupBox`, matching the Modified/Staged/
  Commit History panel styling. Implements the optional `sync_active_repo(...)`
  protocol method — `interface/main_window.py`'s `_start_auto_sync` calls
  this generically on launch/repo-switch, combining `set_repo()` +
  `start_sync()`.
- `commit_dialog.py` — `CommitDialog`: commit message entry (+ amend
  checkbox), shown before the pull→push workflow starts.
- `conflict_dialog.py` — `ConflictResolutionDialog`: per-file keep-ours/
  keep-theirs resolution, shown when a pull hits a merge conflict.
- `log_panel.py` — `LogPanel`: scrolling read-only log output during
  sync/push/pull.
- `git_stream_worker.py` — `GitStreamWorker`: generic `QThread` that
  streams a git command's output line-by-line and emits whatever it
  returns via `finished_ok`. Used for the Sync button's `open_or_sync`
  (clone/pull, also driving `sync_active_repo`'s launch/repo-switch
  auto-sync) as well as the pull and push steps of the commit workflow —
  one generic worker where there used to be a separate `GitWorker` class
  just for `open_or_sync`.
- `status_worker.py` — `RepoStatusWorker`: fetches working-tree status
  (modified/staged/untracked) off the UI thread.
- `commit_log_worker.py` — `CommitLogWorker`: fetches a page of the
  whole-repo commit log (GitHub-API-first, local-git-fallback) off the UI
  thread; shares `CommitCard`/`CommitHistoryEntry` with Explorer via
  `interface/shared/commit_history.py` (that shared helper module stays in
  `interface/`, imported normally by both plugins).

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `interface/shared/` addition, or touches
`interface/main_window.py`'s generic `SectionHost` wiring.
