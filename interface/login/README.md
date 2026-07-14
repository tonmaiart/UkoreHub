# interface/login/

The GitHub login flow and the mandatory startup/quick-start gate — GitHub
login is required before `main_window.py` will let the app run
(`MainWindow._ensure_logged_in` blocks on this at launch and again on
logout).

- `launch_dialog.py` — `LaunchDialog`: the mandatory startup gate. Embeds
  `GitHubAuthWidget` and `RepoPickerDialog`-style repo selection; re-shown
  on every rejected login attempt since the app cannot run unauthenticated.
- `github_login_dialog.py` — `GitHubLoginDialog`: the GitHub OAuth device
  flow modal (shows the user code + verification URL, polls for
  completion via `github_auth_worker.py`).
- `github_auth_widget.py` — `GitHubAuthWidget`: username/avatar display,
  plus an optional Login/Logout toggle button (`show_toggle_button`
  constructor param). `launch_dialog.py` embeds it with the toggle visible
  (login isn't done yet there); `interface/sidebar/sidebar.py`'s footer
  constructs it with `show_toggle_button=False` — Sidebar only ever shows a
  logged-in user, and logout now lives in Settings > Common instead
  (`interface/settings/common_settings_page.py`'s own Logout button, wired
  to the same logout flow in `main_window.py`). Lives here rather than in
  `sidebar/` since its logic is entirely about the auth flow.
- `github_auth_worker.py` — `QThread` that runs the OAuth device-flow
  polling off the UI thread, used by `github_login_dialog.py`.
- `github_avatar_worker.py` — `QThread` that downloads the GitHub avatar
  image off the UI thread, used by `github_auth_widget.py`.
- `repo_picker.py` — `RepoPickerDialog`: the "..." repo picker, used both
  from `launch_dialog.py` (first-time setup) and
  `interface/sidebar/active_repo_widget.py`'s picker button (normal
  operation) — grouped here since `launch_dialog.py` treats it as part of
  the same quick-start flow. Renders one clickable `_RepoCard` per repo —
  name + status sharing one row (status pinned right) rather than a
  `QTreeWidget` with extra columns — click selects (exclusive), double-click
  accepts immediately. When the repo has a thumbnail (`MetadataStore.
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
