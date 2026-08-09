# data/

Runtime data UkoreHub's `core/` stores read and write — not code. See
`core/README.md` (`store.py`, `program_store.py`) and
`core/extensibility/README.md` (`config_store.py`) for the classes that own
these files; this README is just what's on disk and whether it's shared.

**Working here:** don't open these files unless the task specifically needs
their current contents (e.g. debugging a stale value, checking a real id).
Never open an image file in here to "look at it" — there's nothing textual
to read, and it wastes context for zero benefit. Never confuse this with
`projects/` at the repo root, which is the actual gitignored workspace root
(real cloned repos) — see root `CLAUDE.md`; that one is never read at all
unless explicitly asked.

## JSON stores

Shared studio config (below) is no longer git-tracked — each file is now a
**local cache of a Google Cloud Storage blob**, synced by
`core/cloud_sync.py`'s `GcsJsonSync`: pulled fresh on every launch, pushed
back up on every save (see `launcher.py` and `interface/plugin_api.py`'s
`plugin_config_store(shared=True)`). This replaced the old model (tracked
in this repo, distributed via `git pull`/Update and Restart) because that
meant any machine with an uncommitted local edit broke the self-update
`git pull` outright — see `developer/bug-history/` for the incident.

- `projects.json` — `MetadataStore`, the Project/Repo registry.
  **Shared/cloud-synced.** Can grow large as repos/thumbnails accumulate —
  prefer `programs.json`/`system_config.json` below if you just need "an
  example of the shape."
- `programs.json` — `ProgramStore`, the shared software catalog. Shared/
  cloud-synced, small.
- `system_config.json` — `SystemConfigStore`, studio-wide settings: GitHub
  OAuth client id, plus `gcs_bucket_name`/`gcs_project_id`/
  `google_oauth_client_id`/`google_oauth_client_secret` for
  `core/cloud_sync.py`. All non-secret identifiers safe to keep here — the
  Google OAuth client is a "Desktop app" type, whose
  secret isn't meaningfully confidential for a distributed app (same
  reasoning as the GitHub Client ID). Shared/cloud-synced, tiny.
- `projects.example.json` — a checked-in sample shape for `projects.json`,
  not read by the app itself. Still git-tracked (it's a static example, not
  live data).
- `system_config.default.json` — git-tracked bootstrap copy of just the
  two `core/cloud_sync.py` fields an anonymous pull needs
  (`gcs_bucket_name`/`gcs_project_id`). Deliberately excludes
  `google_oauth_client_id`/`google_oauth_client_secret` — GitHub's secret
  scanning flags the client secret, and it's dead weight here anyway: this
  file is only ever consulted when no `refresh_token` exists yet either
  (a genuinely fresh machine), and `GcsJsonSync` only builds `Credentials`
  from client id/secret when `refresh_token` is present. Unlike
  `projects.example.json`, this one **is** read by the app: `launcher.py`'s
  `_build_cloud_sync` falls back to it when the real (gitignored)
  `system_config.json` doesn't exist yet on this machine or lacks
  `gcs_bucket_name` — otherwise a fresh clone could never bootstrap the
  bucket name needed to pull the real `system_config.json` in the first
  place. The first successful pull overwrites `system_config.json` with
  the live cloud copy, so this file only matters before that.
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
Developer — a real secret, never `data/`, which is either git-tracked or,
for the JSON stores above, a cloud-synced cache readable by anyone with
the file). This means `data/` today holds files meant to be the same for
everyone at the studio, whether that sameness comes from git or from the
shared bucket.

## Binary/image directories — not code, skip unless verifying a specific file

- `thumbnails/` — per-repo thumbnail images, filename = `Repo.
  thumbnail_filename`.
- `program_icons/` — per-`Program` icons, filename = `Program.
  icon_filename`.
- `browser_link_icons/` — per-`BrowserLink` icon overrides, filename =
  `BrowserLink.icon_filename`. Falls back to `icons/icons8-browser-50.png`
  when unset.
- `icons/` — static app-chrome icons (Setting gear, Sidebar's
  SectionTabList's About/Browser/Explorer/Submit icons), not tied to any
  JSON store record — just fixed asset files referenced directly by path
  from `interface/`.

All are referenced by filename from the JSON stores above (except `icons/`,
referenced directly by path); if a task needs to confirm a file exists,
check with a directory listing, not by opening the image.
