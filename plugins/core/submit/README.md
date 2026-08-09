# plugins/core/submit/

The Submit tab (`SectionRegistry` key `repo_git_status`) — stage/unstage/
revert, commit → pull → (resolve conflicts) → push. A real always-on
`plugins/core/` plugin (see `core/extensibility/README.md` for how
`manifest.json`/`plugin.py` are discovered/loaded) — not special-cased by
`interface/`, registers into `SectionRegistry` the same way any other
plugin would.

- `manifest.json` — plugin id `submit`, entry point `plugin.py`.
- `plugin.py` — `register(api)`: constructs `RepoGitStatusPage` from
  `api.metadata`/`api.local_config`/`api.git`, registers it as the
  `SectionSpec(key="repo_git_status", order=20, ...)` section. Also wires
  `background_threads` (reaches into `page._git_worker`/`_status_worker`/
  `_stream_worker` for `MainWindow.closeEvent`'s shutdown cleanup) and
  `wire` — connects `sync_started`/`sync_finished`/`sync_failed` to
  `UICommandService.set_status_message` (the sidebar status line) and
  `browse_file_requested` to `UICommandService.navigate_and_focus` (jumps to
  Explorer's `"repo_browser"` section key and calls its optional
  `browse_to_path` protocol method — see
  `plugins/core/explorer/repo_browser_page.py`). See
  `interface/section_registry.py`'s `UICommandService` for why this is a fixed
  set of named callbacks rather than a generic dispatcher.
- `repo_git_status_page.py` — `RepoGitStatusPage`: the top-level Submit
  page. Drives the full sync/commit/pull/push workflow via the workers
  below, and shows the Modified/Staged lists. Both lists' items are
  checkable (`Qt.ItemIsUserCheckable`, `NoSelection` mode) rather than
  row-selected — `_checked_paths(list_widget)` reads whichever items are
  ticked, and Stage/Revert (Modified) and Restore (Staged) act on that set,
  so multiple files can be picked without holding Ctrl/Shift. Each panel
  has its own "Select All" button (`self.select_all_button` for Modified,
  `self.staged_select_all_button` for Staged), both wired to the shared
  `_on_select_all_clicked(list_widget)` — it toggles every item in that
  list to checked, or back to unchecked if all were already checked. The
  Sync/Refresh Status buttons
  live under the log panel inside a "Git Log" `QGroupBox`, matching the
  Modified/Staged panel styling. Implements the optional
  `sync_active_repo(...)` protocol method —
  `interface/main_window.py`'s `_start_auto_sync` calls this generically
  on launch/repo-switch, combining `set_repo()` + `start_sync()`. There is
  no commit-history UI on this tab anymore — see
  `plugins/core/Notification/README.md`'s "Team activity feed" for where
  that moved. Before the very first clone of a repo (`start_sync` sees
  `git_service.is_cloned(dest_path)` is False) and only when the remote is
  a github.com URL, `start_sync` runs `core.github.repo_access.
  check_repo_access` in a `GitStreamWorker` first
  (`_begin_access_check`/`_on_access_checked`) — if the current GitHub
  account can't see the repo, an "Access Denied" dialog fires immediately
  and the clone is never attempted, instead of letting git itself fail with
  an opaque error. A repo that's already cloned, or whose remote isn't
  github.com, skips straight to `_begin_sync_worker` as before.
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
- `status_dot.py` — `RepoStatusDot(QLabel)`: the small colored circle shown
  at the right edge of Submit's own sidebar row — see "Sidebar status dot"
  below.

## Sidebar status dot

`interface/section_registry.py`'s `SectionSpec.trailing_widget_factory` (the
same general-purpose slot `plugins/core/Notification/`'s unread badge uses)
is handed `page.status_dot` in `plugin.py`. `RepoGitStatusPage` owns/updates
it directly — `SectionTabList` only lays it out.

Three states, driven entirely by the existing `refresh_status()` call (Sync,
Refresh Status, and the auto-sync on launch/repo-switch — no extra polling
or network calls added for this):
- **loading** (hidden, no color) — a status check is in flight, or the last
  one is more than 10 minutes stale. `refresh_status()` sets this
  immediately on every call, before the new `RepoStatusWorker` reports back,
  so the dot never shows a stale/wrong-repo color mid-check.
- **dirty** (yellow, `interface.theme`'s `warning`) — `_on_status_ready` saw a
  non-clean `RepoStatus` (untracked/modified/staged present).
- **fresh** (blue, `interface.theme`'s `accent`) — `_on_status_ready` saw a clean
  `RepoStatus`. Only valid for `FRESHNESS_WINDOW_MS` (10 minutes) —
  `_freshness_timer` (restarted on every `refresh_status()` call) flips it
  back to **loading** once that verification goes stale, rather than
  claiming a possibly-outdated "clean" forever between manual
  refreshes/syncs.

There is deliberately no "would conflict on push" state — detecting that
would need a new `git fetch` this page doesn't otherwise do; left out of
scope for now.

`RepoGitStatusPage._on_push_finished` used to push a
`core.extensibility.notification_bus` entry itself on a successful push;
that's gone now — `plugins/core/Notification/`'s own commit-log poll
(`CommitFeedWorker`) picks up every push (this machine's and every
teammate's) as part of its regular team-activity-feed diff, so a
second, submit-local "I just pushed" notification would only be a
near-duplicate. See that plugin's own README for the feed's contract.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, a `interface/shared/` addition, or touches
`interface/main_window.py`'s generic `UICommandService` wiring.
