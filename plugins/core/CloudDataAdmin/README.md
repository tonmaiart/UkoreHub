# plugins/core/CloudDataAdmin/

Settings > Developer tab ("Cloud Data") for directly pulling/pushing one raw
cloud-synced JSON blob (`projects.json`, `programs.json`,
`system_config.json`, or any `plugins/core/*.json`) to/from a file the
artist explicitly chooses — separate from `plugins/core/CloudConfig/`,
which handles login/bucket configuration, not the blobs' actual content.

Exists for the "I have an old `data/` backup, how do I get it back onto the
shared bucket" case — just restoring `data/` locally and reopening UkoreHub
doesn't work, since `launcher.py` always pulls the cloud copy over
`data/*.json` *before* anything gets a chance to read it
(`core/cloud_sync.py`'s `GcsJsonSync.pull` — unconditional overwrite, no
timestamp check), silently clobbering a locally-restored file before it's
ever pushed back up. This plugin's Pull/Push both work on a file chosen via
a file dialog instead, never touching this app's own `data/*.json` — nothing
here takes effect for the running session; restart UkoreHub afterward to
load whatever got pushed. See the `ukorehub-cloud-sync` skill for the
engine this sits on top of.

## Files

- `manifest.json` — plugin id `cloud_data_admin`.
- `plugin.py` — `register(api)`: contributes the "Cloud Data" tab via
  `api.register_settings_tab(...)`, `category=CATEGORY_DEVELOPER`.
- `cloud_data_admin_page.py` — `CloudDataAdminPage`:
  - An editable blob-name combo box, pre-filled with the three fixed
    top-level blobs plus every `data/plugins/core/*.json` filename found
    locally right now (a convenience list, not a constraint — stays
    editable for a blob that hasn't been pulled locally yet).
  - **Pull from Cloud, Save As...** — `GcsJsonSync.pull(blob_name,
    <chosen save path>)`, so an artist can inspect exactly what's live on
    the bucket right now without disturbing this running session's own
    `data/` files.
  - **Open Local Synced File** — opens the selected blob's own local cache
    under `data/` (i.e. `data/<blob_name>` — the exact file this running
    app itself reads/writes, not a file picker) in its OS default app
    (`core/os_utils.py`'s `open_with_default_app`, the same helper
    `plugins/core/explorer/browser_widget.py` uses). Warns instead of
    opening if that blob hasn't synced to this machine yet.
  - **Push File to Cloud...** — picks a local JSON file, confirms (names
    the blob and warns every artist's next launch will pull it), then
    pulls the same blob into a throwaway temp file first (just to refresh
    `GcsJsonSync`'s per-blob generation counter — otherwise a blob this
    session never pulled looks like generation 0, i.e. "must not exist
    yet", and a legitimate overwrite gets rejected as a false conflict)
    before the real `push(blob_name, <chosen file>)`. Surfaces
    `core.exceptions.ConflictError` (someone else pushed in between) and
    any other failure (not logged in, network, timeout) via `QMessageBox`.

## What `plugin.py`/the page reads off `api`

- `api.cloud_sync` — the already-built `GcsJsonSync` engine (added to
  `PluginAPI` for exactly this kind of use — see
  `plugins/core/CloudConfig/README.md`). `None` if cloud sync isn't
  configured/reachable this run; `.can_push` gates the Push button (Pull
  still works against the public-read bucket either way).
- `api.app_root` — to list `data/plugins/core/*.json` for the combo box's
  suggestions.
