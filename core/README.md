# core/

Non-UI logic layer for UkoreHub — no PySide6/Qt imports here. Everything the
`interface/` layer depends on for data and git operations lives in this
folder.

**Working here:** stay inside `core/` unless the change requires updating
an `interface/` call site — don't open `interface/` or `add-on/` files
otherwise. Two subfolders group related files by function — check their own
README first if you're working in either:

- **`github/`** — everything that talks to GitHub (OAuth device flow, REST
  API, token storage). See `core/github/README.md`.
- **`extensibility/`** — the plugin/add-on discovery and hook system. See
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
  commit, stage/unstage, revert, status, conflict resolution, commit log,
  per-commit changed-files (`get_commit_files`). Fires hooks from
  `extensibility/hooks.py` around each operation. Every subprocess call
  passes `CREATE_NO_WINDOW` (Windows-only) so git never flashes a console
  behind the GUI.
- `program_store.py` — the shared Program Database (`data/programs.json`,
  `name`/`version`/`description`/`icon_filename`), pipeline software repos can
  list as requirements.
- `addon_store.py` — `AddonMetadataStore` (`data/addon_settings.json`):
  studio-editable overrides layered on top of a discovered add-on's own
  manifest.json — icon, description override, and which Program(s) it
  requires. Edited via Settings > Add-ons, never by an add-on's own
  `register(api)`. Also has `group_addon_ids_by_program`, the pure helper
  Repo About / the repo editor's add-on picker use to nest add-ons under
  the Program they declare. `resolve_display_icon_path` falls back to
  `DEFAULT_ICON_FILENAME` (`data/addon_icons/icons8-tools-50.png`) for
  add-ons with no icon of their own — used by Repo About's `AddonCard`;
  `resolve_icon_path` itself still returns `None` when unset, for editing
  UIs that need to tell the difference.
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

Note: a `Repo.enabled_addon_ids` field also exists on `models.py`/`store.py`
(`set_repo_enabled_addons`) — this is pure metadata (which discovered
add-ons a repo declares it uses, shown on Repo About and editable in the
repo editor's "Enabled Add-on" picker), not an execution gate; every loaded
plugin/add-on's hooks/sections stay active app-wide regardless. Add-ons are
discovered from a *second*, separate catalog — the top-level `add-on/`
folder (single flat folder, no studio/local split, everything git-tracked) —
using the exact same `extensibility/loader.py` machinery as `plugins/`. The
two catalogs are otherwise independent: `plugins/` is always-on app
features, `add-on/` is the pool a repo picks *from*.
