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

- `models.py` — dataclasses for `Project`, `Repo`, `RepoStatus`, etc.
- `store.py` — `MetadataStore` (reads/writes `data/projects.json`, the
  Project/Repo registry) and `LocalConfigStore`/`SystemConfigStore` (per-machine
  vs. shared settings).
- `git_service.py` — wraps `git`/`git-lfs` subprocess calls: clone, pull, push,
  commit, stage, status, conflict resolution, commit log. Fires hooks from
  `extensibility/hooks.py` around each operation.
- `program_store.py` — the shared Program Database (`data/programs.json`,
  `name`/`version`/`description`/`icon_filename`), pipeline software repos can
  list as requirements.
- `addon_store.py` — `AddonMetadataStore` (`data/addon_settings.json`):
  studio-editable overrides layered on top of a discovered add-on's own
  manifest.json — icon, description override, and which Program(s) it
  requires. Edited via Settings > Add-ons, never by an add-on's own
  `register(api)`. Also has `group_addon_ids_by_program`, the pure helper
  Repo About / the repo editor's add-on picker use to nest add-ons under
  the Program they declare.
- `paths.py` — resolves a repo's on-disk clone path from workspace root +
  project/repo name.
- `theme.py` — color theme definitions and stylesheet generation.
- `os_utils.py` — OS-level helpers (open in file explorer, open with default
  app).
- `self_update.py` — pulls UkoreHub's own repo to self-update.
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
