# appdata/

Static, git-tracked files the app reads as **bootstrap fallbacks or
examples** — never cloud-synced, never written to by the running app. Split
out of `data/` on 2026-08-09 so that `data/` could become "cloud-synced JSON
blob cache, no exceptions" literally, instead of true "except for these two
files" — see `data/README.md`.

- `system_config.default.json` — bootstrap copy of just the two
  `core/cloud_sync.py` fields an anonymous pull needs
  (`gcs_bucket_name`/`gcs_project_id`). Deliberately excludes
  `google_oauth_client_id`/`google_oauth_client_secret` — GitHub's secret
  scanning flags the client secret, and it's dead weight here anyway: this
  file is only ever consulted when no `refresh_token` exists yet either (a
  genuinely fresh machine), and `GcsJsonSync` only builds `Credentials` from
  client id/secret when `refresh_token` is present. **Is** read by the app:
  `launcher.py`'s `_build_cloud_sync` falls back to it when the real
  (gitignored) `data/system_config.json` doesn't exist yet on this machine
  or lacks `gcs_bucket_name` — otherwise a fresh clone could never bootstrap
  the bucket name needed to pull the real `system_config.json` in the first
  place. The first successful pull overwrites `data/system_config.json` with
  the live cloud copy, so this file only matters before that.
- `projects.example.json` — a checked-in sample shape for `data/projects.json`
  — the lightweight index only (`{"id", "name"}` per project, `schema_version`
  2), **not** read by the app itself.
- `project.example.json` — a checked-in sample shape for one project's own
  blob, `data/projects/<project_id>.json` (repos, requirements, pins,
  browser links, plugin_data, and that project's own Program Database) —
  also **not** read by the app itself. Split from `projects.example.json`
  on 2026-08-09 when `MetadataStore` itself split the same way (see
  `data/README.md`) — purely a reference for a human (or an agent) who
  needs "an example of the shape" without pulling the real, possibly-large
  `data/projects/<id>.json`.
