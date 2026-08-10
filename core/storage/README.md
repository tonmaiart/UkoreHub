# core/storage/

The JSON-file stores — no PySide6/Qt imports here (same Qt-free rule as
the rest of `core/`).

- `atomic_file.py` — `atomic_write(path, data)` (tmp-file + `os.replace`,
  shared by every store below and by `core/extensibility/config_store.py`'s
  `PluginConfigStore`) and `utc_now_iso()`.
- `metadata_store.py` — `MetadataStore` (the Project/Repo registry, split on
  disk into a lightweight index — `data/projects.json`, id/name only — plus
  one blob per project under `data/projects/<id>.json`, see
  `data/README.md`), `read_project_ids(json_path)` (used by `launcher.py` to
  know which per-project blobs to pull from GCS before `MetadataStore.load()`
  runs), and `migrate_legacy_programs(store, legacy_path)` (one-time cutover
  from the old studio-wide `data/programs.json` catalog into each Project's
  own `programs` list).
- `config_store.py` — `LocalConfigStore` (per-machine settings — workspace
  root, theme, active project/repo, GitHub username — gitignored) and
  `SystemConfigStore` (studio-wide settings — GitHub OAuth client id, R2
  bucket name — shared via Cloudflare R2, see `core/vcs/README.md`; the R2
  account id/access key/secret themselves never live here, only the
  non-secret bucket name — see `core/vcs/cloud_sync.py`'s module docstring).

**Never import `core.vcs.cloud_sync` from anything in this folder.** These
three stores instead gain an optional `on_save`/`on_delete` constructor
callback that `launcher.py`/`interface/plugin_api.py` wire up to
`R2JsonSync.push`/`.delete` — see `core/vcs/README.md`'s cloud_sync.py
entry for why this isolation is load-bearing (keeping `boto3`
out of `updater.py` (UkoreHubLauncher repo)'s frozen-exe import graph).
