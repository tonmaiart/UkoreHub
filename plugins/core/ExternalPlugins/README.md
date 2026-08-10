# plugins/core/ExternalPlugins/

Settings > Developer > "External Plugins" — a studio-wide catalog of
`cache/plugins/` repo plugins (each its own separate git clone, see
`plugins/README.md`), whether already cloned or not, with Clone/Pull and
an ahead/behind check against each one's remote. Built because
`core/extensibility/README.md` notes there's no auto-fetch/clone
mechanism anywhere else — every `cache/plugins/` entry today was cloned
by hand.

- `manifest.json` — plugin id `external_plugins`.
- `catalog_store.py` — `CatalogEntry` (`id, name, git_url, folder_name`) +
  `ExternalPluginCatalog`, a thin wrapper around a shared (`shared=True`)
  `PluginConfigStore` (`data/plugins/core/external_plugins.json`,
  git-tracked so every machine sees the same catalog after a self-update
  pull) — `list_entries()/add_entry()/edit_entry()/delete_entry()`.
  `folder_name` must be a single safe path segment: it's used directly as
  `cache/plugins/<folder_name>`.
- `catalog_entry_dialog.py` — `CatalogEntryDialog`: Name / Git URL /
  Folder Name fields for Add/Edit, same shape as `interface/settings/
  program_dialog.py`'s `ProgramDialog`.
- `external_plugins_page.py` — `ExternalPluginsPage`: the tab itself.
  Lists every catalog entry plus any `cache/plugins/*` folder that's
  already cloned but not yet in the catalog (auto-detected via
  `GitService.is_cloned`/`get_remote_url`, labeled "(not catalogued)" —
  Edit on one of these adopts it into the catalog instead of editing an
  existing entry). A folder with a `.git` directory that exists but isn't
  actually a valid repo root (`GitService.is_repo_root` returns False —
  e.g. an interrupted/broken clone) shows as its own distinct status
  instead of being treated as usable — see "Why `is_repo_root`, not just
  `is_cloned`" below. Add/Edit/Delete manage the catalog itself; Clone/Pull
  act on the selected row via `GitService.clone`/`pull`; "Check for
  Updates" runs `GitService.fetch` + the new `get_ahead_behind` (see
  `core/README.md`) against every cloned row and updates its status text
  (`Up to date` / `N commit(s) behind` / `N commit(s) ahead (not pushed)`
  / `Diverged`) — also reads `GitService.get_working_tree_status` and
  treats any untracked file as not-up-to-date on its own (even a row with
  no ahead/behind gets `Not up to date — N untracked file(s)` instead of
  `Up to date`), since a Pull alone can't fix that; "Open Git Directory"
  opens the selected row's local clone
  in the OS file explorer via `core/os_utils.py`'s `open_in_file_explorer`
  (no-op with an info message if it isn't cloned yet); "Stage Untracked &
  Push" stages every untracked file (`GitService.stage_paths`), commits
  with a message typed into a plain `QInputDialog` prompt, then pushes
  (`GitService.commit`/`push`) — a bulk "get this repo plugin's new files
  into the remote" action, not a real commit-review workflow (that's
  Submit's job, for a repo, not a repo plugin).
- `plugin.py` — `register(api)`: registers the settings tab
  (`CATEGORY_DEVELOPER`, key `external_plugins`), building a fresh
  `ExternalPluginsPage` per `page_factory` call — same "no long-lived page,
  a new one every time Settings is opened" convention every Settings tab
  uses (see `interface/settings/settings_view.py`'s `SettingsView`
  docstring), so there's nothing here to wire up for shutdown cleanup.
  Threads `api.metadata`/`api.local_config` into the page too — see "Used by
  this Project" below.

## Used by this Project

Added 2026-08-10. This catalog is studio-wide (every entry is visible to
every project), but not every project actually needs every repo plugin — a
`cache/plugins/AdvancedSkeleton` clone one rigging-heavy project needs has no
business showing up as an option for an unrelated project's repos. Each
catalogued entry (not the auto-detected "(not catalogued)" rows — nothing to
mark until they're adopted into the catalog) tracks whether it's "used by"
the *active* project, in `Project.plugin_data["external_plugins"]
["selected_entry_ids"]` (a `list[str]` of catalog entry ids) via
`MetadataStore.get_project_plugin_data`/`set_project_plugin_data` — both
already generic, so this needed no `core/models.py` or
`core/storage/metadata_store.py` changes.

This was originally a manual per-row checkbox; changed same day after
feedback that it was a redundant click — adding a catalog entry (Add) or
adopting an auto-detected on-disk folder (Edit on a "(not catalogued)" row)
only ever happens because the active project needs it, so
`ExternalPluginsPage._auto_select_entry` now marks the entry "used by" the
active project automatically right after either action, with no separate
toggle. A no-op if no project is active yet — there's nothing to persist
the selection against.

`interface/repo_settings/requirements_and_plugins_page.py`'s External column
(Settings > Repo Setting (Dev) > Requirements & Plugins) reads this same
`selected_entry_ids` list (plus this catalog's raw JSON, read directly rather
than importing this plugin's `CatalogEntry` — see that file's own comments)
to decide which `cache/plugins/` repo plugins are even offered as a
requirement choice for the active project's repos, instead of listing every
"repo"-source plugin `discover_plugins()` happens to find physically cloned
on this machine regardless of which project it was cloned for.

A selected-but-not-yet-cloned entry no longer requires a separate trip to
this page to clone it (2026-08-10): its row on Requirements & Plugins is
itself checkable, and checking it clones straight into
`cache/plugins/<folder_name>` immediately (no confirm prompt — the only
git-clone action in the app that skips one, since checking the box already
is the explicit action), then marks it required for that repo by reading
the fresh clone's `manifest.json` directly (no import/execution — just a
`json.loads`, via `RequirementsAndPluginsPage._read_manifest_if_cloned`).
Since `discover_plugins()`/`apply_plugins()` are one-shot at app startup
(see `core/extensibility/README.md`), the plugin still doesn't actually
*load* until UkoreHub is restarted — the row reflects that afterward as
"(installed — restart UkoreHub to activate)" rather than going back to
"(not installed — ...)".

### Showing and cascading `PluginManifest.requires`

Each catalogued row's label also shows `— requires: X, Y` when the entry is
cloned and its `manifest.json` declares `requires` — resolved via
`PluginAPI.plugin_catalog` (the same `discover_plugins()` result the rest of
the app uses; threaded into this page's constructor by `plugin.py`), not by
this page re-parsing `manifest.json` itself. An entry that isn't cloned yet
shows no requires text — there's no manifest to read until it is.
`_auto_select_entry` also cascades: an entry auto-selected whose
requirements resolve to *other* catalogued, cloned External entries marks
those as "used by" the project too, silently (no confirm prompt — see "Used
by this Project" above for why this page dropped the manual-toggle/confirm
shape entirely). A requirement that resolves to a Core/Internal plugin, or
to a plugin this machine hasn't discovered at all, has nothing to
cascade-select on this page — Core is always on and Internal is opted into
per-repo, not per-project.

## Why `is_repo_root`, not just `is_cloned`

`GitService.is_cloned()` only checks that a `.git` entry exists — true
even for an empty/corrupt `.git` directory left by an interrupted clone,
in which case git's own repo-discovery silently walks up to whatever real
repository is further up the tree (in this app's case, UkoreHub's own
repo root) instead of failing. Pull/Check for Updates/Stage Untracked &
Push all gate on `GitService.is_repo_root()` instead (via
`_require_valid_clone()`), which actually confirms `git rev-parse
--show-toplevel` resolves back to the folder itself — see bug-history
2026-08-08, where a broken `cache/plugins/AdvancedSkeleton/.git` almost
caused "Stage Untracked & Push" to commit and push UkoreHub's own
uncommitted local changes into AdvancedSkeleton's remote. A folder that
fails this check shows `Broken .git directory (not a valid clone) —
delete the folder and Clone again` rather than being silently treated as
a normal clone.

## Why no background thread

Opening the tab only does a fast local filesystem pass (cloned vs. not
cloned) — no network call. "Check for Updates" and Clone/Pull do call
git over the network, but run synchronously on the UI thread (with
`QApplication.setOverrideCursor(Qt.WaitCursor)` and a `processEvents()`
after each repo during the bulk check, so the dialog stays visibly
responsive) rather than a `QThread`. Unlike `SectionSpec`,
`SettingsTabSpec` has no `background_threads` shutdown-cleanup hook, and
`SettingsDialog` is rebuilt fresh on every open — adding real threading
would mean extending that shared framework for a handful of small repo
clones that don't need it. If the catalog grows large enough that this
becomes a real wait, that's the trigger to revisit, not before.
