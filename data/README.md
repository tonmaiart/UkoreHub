# data/

Runtime data UkoreHub's `core/` stores read and write — not code. See
`core/README.md` (`store.py`, `program_store.py`) and
`core/extensibility/README.md` (`config_store.py`) for the classes that own
these files; this README is just what's on disk and whether it's shared.

**Working here:** don't open these files unless the task specifically needs
their current contents (e.g. debugging a stale value, checking a real id).
Never open an image file in here to "look at it" — there's nothing textual
to read, and it wastes context for zero benefit. Never confuse `data/projects/`
below (per-project JSON metadata blobs) with `storage/` at the repo root,
the actual gitignored workspace root (real cloned repos, binaries, studio
artwork) — see root `CLAUDE.md`; that one is never read at all unless
explicitly asked. (`storage/` was named that specifically, not `projects/`,
to keep these two unambiguous.)

## JSON stores — cloud-synced only, nothing else belongs here

Every file directly under `data/` (and `data/projects/*.json`,
`data/plugins/core/*.json`) is a **local cache of a Google Cloud Storage
blob**, synced by
`core/cloud_sync.py`'s `GcsJsonSync`: pulled fresh on every launch, pushed
back up on every save (see `launcher.py` and `interface/plugin_api.py`'s
`plugin_config_store(shared=True)`). This replaced the old model (tracked
in this repo, distributed via `git pull`/Update and Restart) because that
meant any machine with an uncommitted local edit broke the self-update
`git pull` outright — see `developer/bug-history/` for the incident.

This is a hard rule, not just the common case: a handful of Maya-side
scripts under `plugins/repo_internal/*/maya-scripts/` (which can't import
`PluginAPI` — no `google-cloud-storage` in `mayapy`'s site-packages) build
these same paths themselves, e.g. `root / "data" / "projects.json"` or
`root / "data" / "plugins" / "core" / f"{tool_id}.json"`. Any file placed
directly under `data/` that *isn't* one of these cloud-synced blobs risks
being mistaken by a future reader (human or not) for one — that's why the
two static git-tracked files that used to live here
(`projects.example.json`, `system_config.default.json`) were moved out to
`appdata/` instead (2026-08-09) — see `appdata/README.md`.

- `projects.json` — `MetadataStore`'s Project/Repo registry, split into a
  **lightweight index** (this file — just `{"id", "name"}` per project) plus
  one blob per project under `projects/<id>.json` (the real payload: each
  project's `repos` with their requirements/pins/browser links/etc., plus
  that project's own `programs` — its Program Database, not shared with
  other projects). Editing one project's repos only ever rewrites and
  pushes that project's own `projects/<id>.json`, never this index or any
  other project's blob — keeps the blast radius (and false-conflict risk
  between artists editing unrelated projects) down as the registry grows.
  **Both shared/cloud-synced.** Prefer `system_config.json` below, or
  `appdata/projects.example.json`/`appdata/project.example.json`, if you
  just need "an example of the shape".
- `projects/<project_id>.json` — one file per project (see above), named
  after the `Project.id` listed in `projects.json`'s index. **Shared/
  cloud-synced**, one GCS blob per file (`projects/<id>.json`).
- `programs.json` — **retired**, no longer read/written by the running app
  except a one-time migration (`core/store.py`'s `migrate_legacy_programs`,
  called once from `launcher.py`). Used to be the shared, studio-wide
  Program Database (pipeline software catalog); each Project now has its
  own instead (`Project.programs`, part of that project's own
  `projects/<id>.json` blob — see `core/models.py`). Still pulled at
  launch and left in place afterward as a manual-reference fallback for
  any Program that no repo required at migration time (nothing to
  automatically re-home it to) — openable via Settings > Developer >
  Cloud Data.
- `system_config.json` — `SystemConfigStore`, studio-wide settings: GitHub
  OAuth client id, plus `gcs_bucket_name`/`gcs_project_id`/
  `google_oauth_client_id`/`google_oauth_client_secret` for
  `core/cloud_sync.py`. All non-secret identifiers safe to keep here — the
  Google OAuth client is a "Desktop app" type, whose
  secret isn't meaningfully confidential for a distributed app (same
  reasoning as the GitHub Client ID). Shared/cloud-synced, tiny.
- `plugins/core/*.json` — `PluginConfigStore` files, one per `plugin_id` a
  plugin's `register(api)` chose with `shared=True`
  (`api.plugin_config_store(plugin_id, shared=True)`). Shared/cloud-synced.
  Named after `shared=True/False`, not after which `plugins/` source root
  the calling plugin itself lives under — a `plugins/repo_internal/` or
  `cache/plugins/` plugin still writes here for `shared=True`. The
  `shared=False` counterpart (per-machine) writes to
  `cache/plugin_local_config/*.json` instead — see `cache/README.md`.

Everything per-machine/gitignored that used to live here
(`local_config.json`, `github_token.json`, `webengine_profile/`,
`plugins/local/*.json`) now lives under `cache/` instead — see
`cache/README.md`. That's also where each artist's own GCS
**credential** lives (`cache/gcs_refresh_token.json`, a per-machine Google
OAuth refresh token obtained via "Login with Google" in Setting >
Developer — a real secret, never `data/`, which is a cloud-synced cache
readable by anyone with the file). This means `data/` today holds exactly
the files meant to be identical for everyone at the studio via the shared
bucket — nothing git-tracked, nothing per-machine.

## Two other things used to live here, moved out on 2026-08-09

- **Binary/image directories** (`thumbnails/`, `program_icons/`,
  `browser_link_icons/`, `icons/`) — now under the repo-root `assets/`
  instead (`MetadataStore.assets_dir`, `launcher.py`'s `assets_dir`) — see
  `assets/README.md`. Git-tracked binary files, not `core/`-owned JSON data.
- **Static git-tracked defaults** (`projects.example.json`,
  `project.example.json`, `system_config.default.json`) — now under the
  repo-root `appdata/` instead — see `appdata/README.md`. Never
  cloud-synced, never written by the running app.

Both moves exist for the same reason: to make "everything directly under
`data/` is a cloud-synced JSON blob cache, no exceptions" a rule a reader
(or the Maya-side scripts above) can rely on literally, instead of one with
asterisks.
