# plugins/core/ExternalPlugins/

Settings > Project > "External Plugins" — the active Project's own
catalog of `cache/plugins/` repo plugins (each its own separate git
clone, see `plugins/README.md`), whether already cloned or not, with
Clone/Pull and an ahead/behind check against each one's remote. Built
because `core/extensibility/README.md` notes there's no auto-fetch/clone
mechanism anywhere else — every `cache/plugins/` entry today was cloned
by hand. A background auto-sync engine (see "Auto-sync engine" below)
now handles the common case of that by itself — this page's manual
actions remain for everything the engine can't or shouldn't do alone
(first-ever clone of a brand new catalog entry, resolving a conflict).

As of 2026-08-11 the catalog itself is per-project, not studio-wide — see
"Per-project catalog, not a studio-wide file" below. Existing entries in
the old shared `data/plugins/core/external_plugins.json` were **not**
migrated (an explicit choice, not an oversight — every project starts
with an empty catalog and each entry has to be re-added per project it's
actually used in); that old file is left on disk, unread by anything now.

- `manifest.json` — plugin id `external_plugins`.
- `catalog_store.py` — `CatalogEntry` (`id, name, git_url, folder_name,
  plugin_id`) + `ExternalPluginCatalog`, a thin wrapper around a
  `ProjectPluginConfigStore` (`core/extensibility/config_store.py`) —
  i.e. the active Project's own
  `Project.plugin_data["external_plugins"]["catalog"]`
  (`core/models.py`), synced the same way the rest of that project's data
  is (`MetadataStore`'s per-project cloud sync, see the
  `ukorehub-cloud-sync` skill) — `list_entries()/add_entry()/edit_entry()/
  delete_entry()/update_plugin_id()`. `config_store` is `None` when no
  project is active yet; every method degrades to a no-op/empty list
  rather than crashing. `folder_name` must be a single safe path segment:
  it's used directly as `cache/plugins/<folder_name>`. `plugin_id` is a
  cache of "what `PluginManifest.id` does this entry produce once cloned",
  unknown until some machine's auto-sync engine or the Requirements &
  Plugins manual clone-on-check flow backfills it — see "Auto-sync engine"
  below for why this exists.
- `catalog_entry_dialog.py` — `CatalogEntryDialog`: Git URL / Name /
  Folder Name fields for Add/Edit, same shape as `interface/settings/
  program_dialog.py`'s `ProgramDialog`. Name and Folder Name auto-fill
  from the Git URL (`core/vcs/paths.py`'s `extract_git_repo_name`) the
  moment a URL is typed, as long as the user hasn't already typed
  something into that field themselves — so adding an entry is usually
  just pasting a Git URL. Never exposes `plugin_id` — it's derived/cached,
  not something a human sets.
- `sync_engine.py` — Qt-free sync logic: `resolve_required_entries()`
  (which catalog entries the active repo's `Repo.required_plugin_ids`
  resolves to, via each entry's `plugin_id`) and `sync_entry()`
  (clone-if-missing / pull-if-present / conflict-check for one entry).
- `sync_worker.py` — `ExternalPluginSyncWorker(QThread)`: runs
  `sync_engine` for a batch of entries sequentially, off the UI thread,
  emitting `entry_synced`/`backfill_ready` signals rather than writing
  anywhere directly.
- `sync_status_store.py` — `ExternalPluginSyncStatusStore`: per-machine
  (`shared=False`) record of the sync engine's last conflict/error result
  per entry, so it survives until someone opens this tab.
- `external_plugins_page.py` — `ExternalPluginsPage`: the tab itself.
  Lists only the active Project's own catalog entries — no disk scan for
  an already-cloned `cache/plugins/*` folder the catalog doesn't mention;
  an entry has to be added here explicitly before it exists anywhere else
  in the app (Requirements & Plugins, the auto-sync engine). A folder with
  a `.git` directory that exists but isn't actually a valid repo root
  (`GitService.is_repo_root` returns False — e.g. an interrupted/broken
  clone) shows as its own distinct status instead of being treated as
  usable — see "Why `is_repo_root`, not just `is_cloned`" below. Every
  row's status (`_local_status`) also folds in the auto-sync engine's last
  result for that entry — `Update Conflict`, `Pending Restart`, or a
  failed auto-clone/-update message — see "Auto-sync engine" below.
  Add/Edit/Delete manage the catalog itself; Clone/Pull act on the
  selected row via `GitService.clone`/`pull` (a successful manual Pull
  also clears any stale conflict/error the engine had recorded for that
  entry); "Check for
  Updates" runs `GitService.fetch` + the new `get_ahead_behind` (see
  `core/README.md`) against every cloned row and updates its status text
  (`Up to date` / `N commit(s) behind` / `N commit(s) ahead (not pushed)`
  / `Diverged`) — also reads `GitService.get_working_tree_status` and
  treats any untracked file as not-up-to-date on its own (even a row with
  no ahead/behind gets `Not up to date — N untracked file(s)` instead of
  `Up to date`), since a Pull alone can't fix that; "Open Git Directory"
  opens the selected row's local clone
  in the OS file explorer via `core/os_utils.py`'s `open_in_file_explorer`
  (no-op with an info message if it isn't cloned yet — also how a dev
  reaches an `Update Conflict` row to resolve it, this page builds no
  in-app conflict-resolution UI of its own); "Stage Untracked &
  Push" stages every untracked file (`GitService.stage_paths`), commits
  with a message typed into a plain `QInputDialog` prompt, then pushes
  (`GitService.commit`/`push`) — a bulk "get this repo plugin's new files
  into the remote" action, not a real commit-review workflow (that's
  Submit's job, for a repo, not a repo plugin).
- `plugin.py` — `register(api)`: registers the settings tab
  (`CATEGORY_PROJECT`, key `external_plugins`), building a fresh
  `ExternalPluginsPage` per `page_factory` call — same "no long-lived page,
  a new one every time Settings is opened" convention every Settings tab
  uses (see `interface/settings/settings_view.py`'s `SettingsView`
  docstring). Also builds `_SyncController` once per app session — see
  "Auto-sync engine" below — which is the one long-lived thing in this
  plugin; its `ExternalPluginCatalog` is built once too
  (`api.project_plugin_config_store(PLUGIN_ID)`), safe to hold for the
  whole session because the active project never changes mid-session
  (switching projects means a full app restart — see
  `core/storage/config_store.py`'s `LocalConfigStore.set_active_project`).

## Auto-sync engine

A repo's required `cache/plugins/` entries clone/update themselves
automatically at app start and on every repo switch, instead of waiting
for someone to open this tab and click Clone/Pull by hand.
`plugin.py`'s `register(api)` subscribes `_SyncController.on_lifecycle_event`
to both `api.on_app_start`/`api.on_repo_changed` (`interface/plugin_api.py`,
fired from `interface/main_window.py`'s `_start_app`/`_set_active_repo`) —
this is the entire lifecycle wiring; nothing outside this plugin folder
needed to change.

- **Resolving "required but never cloned here"**: `Repo.required_plugin_ids`
  stores a plugin's *manifest id*, only learned by reading `manifest.json`
  after a clone exists (see `interface/repo_settings/
  requirements_and_plugins_page.py`'s `_on_catalog_entry_checked`). A
  machine that's never cloned a given entry has no other way to map a
  required manifest id back to that entry's `git_url`/`folder_name` — so
  `CatalogEntry.plugin_id` caches that mapping, backfilled the first time
  `sync_engine.resolve_required_entries()` sees the entry already
  discovered this session (matched by `folder_name`, via the same
  `plugin_catalog` `loader.discover_plugins()` already produced at
  startup — no extra manifest.json parsing) and written back through the
  shared catalog store, so once any one machine backfills it, every other
  machine's next catalog pull can resolve it too. A required manifest id
  with no `plugin_id` mapping anywhere yet just doesn't auto-clone until
  some machine backfills it (e.g. via the existing manual checkbox flow) —
  degrades gracefully, never crashes.
- **Runs on a background thread, not this page's synchronous pattern**:
  see "Why no background thread" below — that section is about this
  page's own deliberate, one-at-a-time button clicks, which is a different
  situation from an automatic sync firing on every app start and repo
  switch. `ExternalPluginSyncWorker` (`sync_worker.py`) is a real `QThread`,
  modeled on `plugins/core/submit`'s worker classes and
  `plugins/core/project_editor/required_repo_clone_worker.py`'s "QThread
  wraps a sequential clone/pull batch" shape. It only ever emits signals —
  `_SyncController` (in `plugin.py`) is the only thing that writes to the
  catalog (`update_plugin_id`) or the status store, and always on the main
  thread (Qt queues a cross-thread signal onto the receiving object's own
  thread automatically), so there's no locking anywhere in this engine.
- **Never overlaps two syncs on the same folder**: `_SyncController` runs
  at most one `ExternalPluginSyncWorker` at a time. A trigger that arrives
  mid-run replaces `_pending_context` (keeping only the latest) instead of
  starting a second worker; the in-flight worker's `finished` signal starts
  exactly one more run for that latest context once it completes — so a
  rapid double repo-switch still eventually syncs the repo actually left
  active, without two `git pull`s ever racing on the same
  `cache/plugins/<folder>` clone.
- **Conflict detection reuses existing `GitService` primitives** —
  `has_unresolved_merge()` (checks `.git/MERGE_HEAD`) and the same
  `GitOperationError`-on-failure contract `pull()` already had. `sync_entry()`
  never force-pushes, aborts a merge, or discards anything: a conflict is
  left exactly as git leaves it, reported as `Update Conflict`, and
  re-detected (not re-attempted) on every later sync until a dev resolves
  it by hand via "Open Git Directory".

## Per-project catalog, not a studio-wide file

`interface/repo_settings/requirements_and_plugins_page.py`'s External column
(Settings > Repo Setting (Dev) > Requirements & Plugins) lists every
`cache/plugins/` repo plugin `discover_plugins()` finds cloned on this
machine, plus every catalog entry the *active project* has that isn't
cloned/discovered yet (`RequirementsAndPluginsPage._read_external_catalog()`
reads `self.store.get_project_plugin_data(project_id, "external_plugins")`
directly — same `MetadataStore` instance this plugin's own
`ProjectPluginConfigStore` reads/writes through, so an edit made on the
External Plugins tab is visible here immediately, no caching on either
side).

Before 2026-08-11 this was one studio-wide catalog
(`data/plugins/core/external_plugins.json`, `shared=True`
`PluginConfigStore`) shown identically to every project, plus a same-day,
twice-reverted attempt at a per-project *selection filter* layered on top
of that one shared file (a "Used by this Project" checkbox, then an
auto-select-on-add version — see prior git history for the full story if
needed). Both filter attempts shared the same flaw: entries already in the
catalog before the filter existed had no way to gain a selection record,
so an existing project's External list could go silently empty even
though the shared catalog itself was full.

Moving the catalog itself into `Project.plugin_data` (this file's own
`ExternalPluginCatalog`, see above) removes that whole bug class rather
than fixing it a third time: there is no filter sitting on top of a shared
list anymore, so there's nothing for a pre-existing record to fail to
match against — each project's catalog **is** its own list, empty by
default. The cost is the flip side of the same design: nothing carries
over from the old shared file automatically. That old file
(`data/plugins/core/external_plugins.json`) is left on disk untouched but
unread — the 5 entries it had (`maya_launcher`, `UkoreReferenceEditor`,
`PublishApi`, `MayaToolkit`, `MayaFileBrowser`) need re-adding by hand to
whichever project(s) actually use them, an explicit choice made when this
migration shipped (2026-08-11), not an oversight.

A selected-but-not-yet-cloned entry doesn't require a separate trip to this
page to clone it: its row on Requirements & Plugins is itself checkable,
and checking it clones straight into `cache/plugins/<folder_name>`
immediately (no confirm prompt — the only git-clone action in the app that
skips one, since checking the box already is the explicit action), then
marks it required for that repo by reading the fresh clone's
`manifest.json` directly (no import/execution — just a `json.loads`, via
`RequirementsAndPluginsPage._read_manifest_if_cloned`). Since
`discover_plugins()`/`apply_plugins()` are one-shot at app startup (see
`core/extensibility/README.md`), the plugin still doesn't actually *load*
until UkoreHub is restarted — the row reflects that afterward as
"(installed — restart UkoreHub to activate)" rather than going back to
"(not installed — ...)".

### Showing `PluginManifest.requires`

Each catalogued row's label also shows `— requires: X, Y` when the entry is
cloned and its `manifest.json` declares `requires` — resolved via
`PluginAPI.plugin_catalog` (the same `discover_plugins()` result the rest of
the app uses; threaded into this page's constructor by `plugin.py`), not by
this page re-parsing `manifest.json` itself. An entry that isn't cloned yet
shows no requires text — there's no manifest to read until it is. On
Requirements & Plugins, checking a plugin whose `requires` aren't all
enabled yet for that repo prompts to enable the closure too (see that
file's `_confirm_and_enable_requirements`) — there's no equivalent
cascade here, since this page has nothing per-repo or per-project left to
cascade into.

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

## Why no background thread (for this page's own manual actions)

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

This reasoning is specific to *this page's* deliberate, one-click-at-a-time
actions (this tab is rarely open, and each action is a single explicit
click). The auto-sync engine (see "Auto-sync engine" above) is a different
situation — it fires unattended on every app start and repo switch and may
need to touch several plugins over the network, so it deliberately does use
a real `QThread` (`sync_worker.py`) rather than repeating this page's
synchronous pattern.
