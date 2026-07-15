# interface/login/

The GitHub login flow and the mandatory startup/quick-start gate — GitHub
login is required before the app is usable
(`MainWindow._show_login_gate` shows the gate at launch and again on
logout, via `_on_initial_login_completed`/`_on_relogin_completed`).

- `login_overlay.py` — `LoginOverlay`: the mandatory login gate. A plain
  `QWidget` (not a `QDialog`) that `main_window.py` sets as its central
  widget by itself, instead of a separate popup window *and* instead of
  drawing it on top of the real main UI — the sidebar/pages/Settings aren't
  constructed at all until login succeeds (`MainWindow._build_main_ui`),
  so there's nothing underneath the gate to cover or fight over z-order/
  painting with. On logout, the real main UI is detached via
  `takeCentralWidget()` (not deleted) and restored the same way once
  relogin completes, rather than rebuilt from scratch. Just the "Login with
  Github" button; on success `MainWindow` auto-opens `RepoPickerDialog`
  right after (Cancel button relabeled "Skip" for that flow) rather than
  this widget having its own project-picking step.
- `github_login_dialog.py` — `GitHubLoginDialog`: the GitHub OAuth device
  flow modal (shows the user code + verification URL, polls for
  completion via `github_auth_worker.py`).
- `github_auth_widget.py` — `GitHubAuthWidget`: display-only username/
  avatar widget, no login/logout control of its own, used by
  `interface/sidebar/sidebar.py`'s footer — Sidebar only ever shows a
  logged-in user, and logout lives in Settings > Common instead
  (`interface/settings/common_settings_page.py`'s own Logout button, wired
  to the same logout flow in `main_window.py`). `login_overlay.py` doesn't
  reuse this widget — it only ever shows the logged-out state, so it just
  has its own plain "Login with Github" button. Lives here rather than in
  `sidebar/` since its logic is entirely about the auth flow.
- `github_auth_worker.py` — `QThread` that runs the OAuth device-flow
  polling off the UI thread, used by `github_login_dialog.py`.
- `github_avatar_worker.py` — `QThread` that downloads the GitHub avatar
  image off the UI thread, used by `github_auth_widget.py`.
- `repo_picker.py` — `RepoPickerDialog`: the "..." repo picker, used both
  right after login (`main_window.py`'s `_offer_repo_pick_after_login`,
  Cancel button relabeled "Skip") and from
  `interface/sidebar/active_repo_widget.py`'s picker button (normal
  operation) — grouped here since the post-login flow treats it as part of
  the same quick-start step. Renders one clickable `_RepoCard` per repo —
  name + status sharing one row (status pinned right) rather than a
  `QTreeWidget` with extra columns — click only selects (exclusive); the
  dialog is accepted solely via its own OK button, deliberately not on
  double-click, so a stray double-click can't jump into the wrong repo.
  Pass `cancel_button_text` to relabel the Cancel button for a given call
  site (e.g. "Skip" right after login). Pass `allowed_pairs` (a
  `set[tuple[project_id, repo_id]]`) to narrow which repos get a card at
  all — `None` (default) shows every repo in the registry; a caller that
  wants a restricted pick (e.g.
  `plugins/studio/explorer/explorer_settings_page.py`'s "Add Pinned
  Repo...", limited to the active repo's declared pipeline inputs/outputs)
  passes the specific pairs instead. When the repo has a thumbnail (`MetadataStore.
  resolve_thumbnail_path`), the card paints it fill-cropped as its own
  background with a dark dimming overlay (`_RepoCard.paintEvent`) so the
  text stays legible — `core/theme.py`'s `QFrame#repoCard[hasThumbnail=
  "true"]` gives the card a transparent QSS background so that custom
  painting isn't erased, same technique as
  `interface/sidebar/active_repo_widget.py`'s `_ThumbnailBanner`. The
  selection ring on a thumbnail card is drawn by hand in `paintEvent` too
  (`_ACCENT_COLOR`, from `core/theme.py`'s single defined theme) rather than
  via QSS `border` — that didn't reliably paint over a transparent
  background, so plain (non-thumbnail) cards still get their border from
  `QFrame#repoCard[selected="true"]` in `core/theme.py`, but thumbnail cards
  don't rely on it. Doesn't use `interface/shared/project_repo_tree.py` —
  that's for the admin/status tree views in Settings, a different UI shape.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive (see `core/github/README.md` for the OAuth/token-storage
side this UI drives) or touches `main_window.py`'s wiring.
