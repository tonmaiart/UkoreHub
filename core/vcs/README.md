# core/vcs/

Version control and sync — everything that talks to git, GitHub, or Google
Cloud Storage on the wire. No PySide6/Qt imports here.

- `git_service.py` — `GitService`: wraps `git`/`git-lfs` as subprocess calls
  (clone, pull, push, fetch, commit, stage/unstage, revert, status,
  conflict resolution, commit log, a stricter `is_repo_root()` clone check
  — see bug-history 2026-08-08 for why `is_cloned()` alone isn't safe to
  gate a mutating call on). Fires hooks from `core/events/hooks.py` around
  each operation. Every subprocess call passes `CREATE_NO_WINDOW`
  (Windows-only) so git never flashes a console behind the GUI.
- `cloud_sync.py` — `GcsJsonSync`: pulls/pushes the shared JSON stores
  (`core/storage/`'s `MetadataStore`/`SystemConfigStore`, and `shared=True`
  `PluginConfigStore` instances) to/from Google Cloud Storage. Uses GCS
  object-generation preconditions for optimistic-concurrency conflict
  detection (raises `ConflictError` on a losing race). **Deliberately
  isolated — only `launcher.py` and `interface/plugin_api.py` import it,
  never anything in `core/storage/` or `core/extensibility/config_store.py`
  themselves, so `google-cloud-storage` never ends up in `updater.py`
  (UkoreHubLauncher repo)'s frozen-exe import graph.** Those stores instead
  gain an optional `on_save`/`on_delete` constructor callback that
  `launcher.py`/`plugin_api.py` wire up to `push`/`delete`. `core/app_core.py`'s
  `UkoreCore` follows the same rule — it never imports this module either.
- `paths.py` — `resolve_repo_path(workspace_root, project_name, repo_name)`
  and `sanitize_folder_name(name)`. **Read
  `developer/bug-history/2026-07-20-repo-path-resolved-from-stale-name.md`
  before adding a new call site** — `resolve_repo_path` is a
  creation-time-only helper (correct only for `core/storage/metadata_store.py`'s
  `add_repo`); any other caller resolving an *existing* repo's folder
  should use `repo.local_path` instead.
- `commits_api.py` — REST calls against `api.github.com` for a path's
  commit history (preferred over local `git log` when reachable — see
  `interface/shared/commit_history.py`) and a generic `download_bytes(url)`.
- `repo_access.py` — `check_repo_access(owner, repo, token)`: a lightweight
  `GET /repos/{owner}/{repo}` used to predict whether a clone would succeed
  *before* attempting one.

`commits_api.py`/`repo_access.py` moved here from the old `core/github/`
folder (2026-08-09 reorg) — they're version-control operations that happen
to go over REST instead of subprocess, not really a separate "auth"
concern; `core/auth/` only holds credential storage and login flows now.
