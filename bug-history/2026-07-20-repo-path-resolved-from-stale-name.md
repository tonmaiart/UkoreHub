# Playblast written into the wrong repo folder after a rename (systemic)

## Symptom

A Maya playblast completed successfully (no error shown to the artist),
but clicking Refresh in UkoreShot's video library never showed the new
file. The repo in question (`AnimatorTeam`) had been renamed from
`KafkaProj` after creation.

## Root cause

`core/paths.py`'s `resolve_repo_path(workspace_root, project_name,
repo_name)` computes a repo's on-disk folder by sanitizing and joining the
**current** project/repo *names*:

```python
def resolve_repo_path(workspace_root, project_name, repo_name) -> Path:
    return Path(workspace_root) / sanitize_folder_name(project_name) / sanitize_folder_name(repo_name)
```

This is only correct **at repo-creation time** — `core/store.py`'s
`add_repo` calls it once to compute the *initial* `Repo.local_path`, which
is then stored permanently and never recomputed on rename (renaming a
repo, `set_repo_name`-equivalent, only ever changes `Repo.name`, not
`Repo.local_path` or anything on disk). Any code that calls
`resolve_repo_path` again later — instead of reading the already-stored
`repo.local_path` — silently computes the *wrong* folder for any repo
renamed after creation, since the name-based path no longer matches where
the repo actually lives on disk.

Confirmed via this repo's own git history:
`data/projects.json`'s `AnimatorTeam` repo was renamed from `KafkaProj` on
2026-07-14; `local_path` still reads `"MerderaProject/KafkaProj"`.
`plugins/studio/PublishApi/maya-scripts/PublishApi/repo_paths.py`'s
`get_active_repo()`/`resolve_ref()` both recomputed via
`resolve_repo_path(..., project.name, repo.name)` instead of reading
`repo.local_path` — resolving to `.../AnimatorTeam/...` (freshly created
by `os.makedirs`, since the caller doesn't check existence first) instead
of the repo's real `.../KafkaProj/...` folder. Every Publisher plugin
built on `PublishApi` (ModelPublisher, RigPublisher, AnimationPublisher,
UkoreBrowser) shared this same latent bug.

The same bug independently existed in
`plugins/studio/project_editor/project_graph_view.py`'s `_is_repo_cloned`
(used for the Viewgraph's clone-status icon) — same recompute-from-name
pattern, same fix.

## Fix

- `plugins/studio/PublishApi/maya-scripts/PublishApi/repo_paths.py`:
  `get_active_repo`/`resolve_ref` now build the path as
  `Path(local_config.workspace_root) / repo.local_path` instead of calling
  `resolve_repo_path`.
- `plugins/studio/project_editor/project_graph_view.py`'s
  `_is_repo_cloned`: same fix.
- `core/paths.py`'s `resolve_repo_path` itself was left unchanged — it's
  correct for its one legitimate use (`core/store.py`'s `add_repo`, at
  creation time, before `local_path` exists).
- **Not yet fixed** (flagged as a separate task, same bug pattern
  confirmed present but not yet verified/fixed one by one):
  `interface/main_window.py`, `interface/settings/local_repository_page.py`,
  `plugins/studio/explorer/repo_browser_page.py`,
  `plugins/studio/submit/repo_git_status_page.py`,
  `plugins/studio/maya_launcher/plugin.py` — all call `resolve_repo_path`
  outside of repo-creation. Check whether this file has been resolved
  before assuming it still needs auditing.

## Lesson

**Never call `core.paths.resolve_repo_path(workspace_root, project_name,
repo_name)` for a repo that already exists.** It's a name-based
*creation-time* helper, not a general "where does this repo live" lookup
— once a `Repo` record exists, its real on-disk location is
`Path(workspace_root) / repo.local_path`, full stop, regardless of
whatever the repo is named *now*. If you're writing code that resolves a
repo's folder and you have a `Repo` object (or can fetch one via
`store.get_repo(project_id, repo_id)`), always use `repo.local_path`.
Grep for `resolve_repo_path` before adding a new repo-path resolution
anywhere in this codebase — if a hit isn't inside `core/store.py`'s
`add_repo`, it's very likely the same bug.
