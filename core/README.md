# core/

Non-UI logic layer for UkoreHub — no PySide6/Qt imports here. Everything the
`interface/` layer depends on for data and git operations lives in this
folder.

**Working here:** stay inside `core/` unless the change requires updating
an `interface/` call site — don't open `interface/` files otherwise. Two
subfolders group related files by function — check their own README first
if you're working in either:

- **`github/`** — everything that talks to GitHub (OAuth device flow, REST
  API, token storage). See `core/github/README.md`.
- **`extensibility/`** — the plugin discovery and hook system. See
  `core/extensibility/README.md`.

Everything else stays flat here since it doesn't form a natural cluster
beyond "core infrastructure":

- `models.py` — dataclasses for `Project`, `Repo` (including
  `browser_links: list[BrowserLink]`, repo-scoped bookmarks rendered as
  their own top-level tab — see `interface/about/browser_link_page.py`),
  `RepoStatus`, etc.
- `store.py` — `MetadataStore` (reads/writes `data/projects.json`, the
  Project/Repo registry, including `set_repo_browser_links`) and
  `LocalConfigStore`/`SystemConfigStore` (per-machine vs. shared settings).
- `git_service.py` — wraps `git`/`git-lfs` subprocess calls: clone, pull, push,
  fetch (remote-tracking refs only, no merge — used by Notification's
  background commit poll so it never touches the working tree), commit,
  stage/unstage, revert, status, conflict resolution, commit log (optional
  `ref=` to log `origin/<branch>` instead of local HEAD), per-commit
  changed-files (`get_commit_files`), ahead/behind counts vs. upstream
  (`get_ahead_behind`, `None` if no upstream), a raw `origin` URL lookup
  (`get_remote_url`), and a stricter clone check (`is_repo_root` —
  confirms `local_path` is really a repo's own root, not just that a
  `.git` entry exists there; see bug-history 2026-08-08 for why
  `is_cloned()` alone isn't safe to gate a mutating git call on) — all
  used by `plugins/core/ExternalPlugins/`. Fires hooks from
  `extensibility/hooks.py` around each operation. Every subprocess call
  passes `CREATE_NO_WINDOW` (Windows-only) so git never flashes a console
  behind the GUI.
- `program_store.py` — the shared Program Database (`data/programs.json`,
  `name`/`version`/`description`/`icon_filename`), pipeline software repos can
  list as requirements.
- `paths.py` — resolves a repo's on-disk clone path from workspace root +
  project/repo name.
- `theme.py` — color theme definitions and stylesheet generation.
- `os_utils.py` — OS-level helpers (open in file explorer, open with default
  app).
- `self_update.py` — pulls UkoreHub's own repo to self-update; also exposes
  `run_git`, a bare synchronous `git <args>` helper against an arbitrary
  `cwd` (as opposed to `git_service.py`'s `GitService`, which is built
  around cloning/syncing *studio project* repos with token auth and hooks).
- `exceptions.py` — shared exception types (`UkoreHubError`, `ValidationError`,
  `NotFoundError`, `GitOperationError`, `GitHubAuthError`).
- `version.py` — app name/version constants.

Note: `Repo.active_plugin_ids` (`set_repo_active_plugin_ids`) is no longer
read anywhere (2026-08-04 — every `plugins/core/` plugin is
unconditionally visible for every repo now, see
`interface/main_window.py`'s `_apply_plugin_visibility`); the field is
kept purely so existing persisted JSON with this key still round-trips
cleanly. `Repo.required_plugin_ids` (`set_repo_required_plugin_ids`) is
the real UI-visibility gate now, for `plugins/repo_internal/` and
`cache/plugins/` entries — hides a plugin's sidebar section unless the
repo's `required_plugin_ids` lists that plugin's id. Edited via
Settings > (repo) > Requirements & Plugins
(`interface/repo_settings/requirements_and_plugins_page.py`).

A second field, `Repo.browser_links` (`set_repo_browser_links`,
`core/models.py`'s `BrowserLink`) is a different shape again: each entry
becomes its own **dynamic sidebar tab** while the owning repo is active,
rebuilt from scratch on every repo switch by `interface/main_window.py`'s
`_rebuild_dynamic_tabs` (`interface/about/browser_link_page.py`'s
`BrowserLinkPage`). Edited via Settings > (repo) > Browser. Unlike
`active_plugin_ids`, this doesn't hide anything that exists elsewhere — it
*adds* tabs that only exist because the link record does. (A sibling
Explorer-pin mechanism used to work the same way — `Repo.explorer_pins`/
`ExplorerPin` — but Add-Pinned-Repo was removed as no longer needed; see
git history if it needs to come back.)
