# appdata/

Static, git-tracked files the app reads as **bootstrap fallbacks or
examples** — never cloud-synced, never written to by the running app. Split
out of `data/` on 2026-08-09 so that `data/` could become "cloud-synced JSON
blob cache, no exceptions" literally, instead of true "except for these two
files" — see `data/README.md`.

- `system_config.default.json` — bootstrap copy of just the one
  `core/vcs/cloud_sync.py` field a fresh pull needs (`r2_bucket_name`) —
  non-secret, safe to commit; the actual R2 account id/access key/secret
  never live in any JSON file at all (see
  `developer/launcher/launcher_build/r2_credentials.py` and the
  `ukorehub-cloud-sync` skill). **Is** read by the app: `launcher.py`'s
  `_build_cloud_sync` falls back to it when the real (gitignored)
  `data/system_config.json` doesn't exist yet on this machine or lacks
  `r2_bucket_name` — otherwise a fresh clone could never bootstrap the
  bucket name needed to pull the real `system_config.json` in the first
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
