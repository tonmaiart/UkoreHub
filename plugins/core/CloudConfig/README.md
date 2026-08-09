# plugins/core/CloudConfig/

The Studio Setting UI for cloud sync — lets an artist log in with Google
and configure the GCS bucket/project/OAuth client that `core/cloud_sync.py`
syncs `data/projects.json`/`programs.json`/`system_config.json`/shared
`PluginConfigStore` files through. This plugin owns only the **UI** half;
the sync **engine** (`core/cloud_sync.py`'s `GcsJsonSync`, `core/google_auth.py`'s
OAuth login + `GoogleTokenStore`) deliberately stays in `core/` and is not
part of this plugin — `launcher.py` has to build it and pull the shared
blobs *before* constructing `MetadataStore`/`ProgramStore`/
`SystemConfigStore`, which itself happens before plugin discovery runs.
A plugin's `register(api)` can never execute early enough to supply that
engine at boot, so there was no way to move it here without inverting the
documented `core -> plugin` dependency direction. See the
`ukorehub-cloud-sync` skill for the full engine architecture.

## Files

- `manifest.json` — plugin id `cloud_config`.
- `plugin.py` — `register(api)`: contributes a "Studio" button into
  Sidebar's footer via `api.register_sidebar_footer_action(...)` (this is
  the first real consumer of that registry — previously only Sidebar's
  hardcoded gear Setting button lived there, so this button now renders as
  its own footer row rather than inline next to the gear icon). Clicking
  it constructs a fresh `StudioSettingsDialog` and shows it modally.
- `studio_settings_dialog.py` — `StudioSettingsDialog`: the login-gate (no
  Google refresh token cached yet) + full-form (bucket/project/OAuth
  client fields, explicit Save button) window, moved here unchanged from
  its old home at `interface/settings/studio_settings_dialog.py`.

## What `plugin.py` reads off `api`

- `api.system_config_store` — the shared, cloud-synced `SystemConfigStore`
  whose `gcs_*`/`google_oauth_*` fields this dialog reads and writes.
- `api.cache_dir` — UkoreHub's per-machine `cache/` directory, used to
  construct `core/google_auth.py`'s
  `GoogleTokenStore(api.cache_dir / "gcs_refresh_token.json")`.

Both were added to `PluginAPI` (`interface/plugin_api.py`) specifically for
this plugin — along with a read-only `api.cloud_sync` property exposing the
already-built `GcsJsonSync` engine itself, for any other Core code or
future plugin that wants to check `api.cloud_sync is not None` or use it
directly, without reaching into `launcher.py`'s internals.
