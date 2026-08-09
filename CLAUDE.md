# UkoreHub

Pipeline tool to launch/sync projects in Ukore Studio — a Git repo launcher
built on PySide6. See [README.md](README.md) for the full project overview,
prerequisites, and config split (system vs. local).

**Before acting on a casual/colloquial term the user uses for a feature**
(e.g. "the program's setting", "Viewgraph", "Custom Path") **or before
asking a clarifying question about one, read
[developer/GLOSSARY.md](developer/GLOSSARY.md)
first** — it maps terms that are easy to misread onto the actual feature/
file, recorded specifically because one of these got misread once already
(see its own entries for the incidents). If a term isn't in there and the
mapping is genuinely ambiguous, ask the user rather than guessing — and
add the resolved mapping to `developer/GLOSSARY.md` afterward so it doesn't need
asking again.

**Before changing code in a file or area listed in
[developer/bug-history/README.md](developer/bug-history/README.md)'s index, read that entry
first** — each one ends with a "Lesson" describing a reusable mistake
pattern (e.g. a specific circular-import shape, a specific stale-path
bug), not just a one-off incident. After fixing any real bug (a crash, a
silent failure, wrong behavior — not a feature change), add a new entry
there following its own "Adding a new entry" format, so the next change
in that area doesn't reintroduce it.

## Reading this codebase

Before exploring a folder's `.py` files, check whether it has its own
`README.md` (e.g. [core/README.md](core/README.md),
[interface/README.md](interface/README.md)) and read it first — it gives a
short, current summary of what that folder is responsible for and how its
files relate, which makes the individual files much faster to place in
context.

**Every folder should have a `README.md`.** This is a token-budget rule,
not just documentation: a good folder README lets a session understand
what's inside without opening every file in it. When you create a new
folder (a new `plugins/core/<Name>/`, a new subfolder under `core/` or
`interface/`), add a short `README.md` to it in the same style as the
existing ones (see `core/README.md` for the reference tone/format — a
short intro paragraph, then a flat bullet list of what each file/subfolder
does and how they relate).

## Scoped editing — stay inside the folder the task names

When a task is about one specific area — a single `plugins/core/<Name>/`,
`plugins/repo_internal/<Name>/`, or `cache/plugins/<Name>/`, `core/`, or
`interface/` — read and edit only that folder. Don't open sibling folders
"just in case" unless the task genuinely crosses the boundary (e.g. a
`core/` change whose call sites in `interface/` also need updating).
Concretely:
- Told to fix/change a plugin (Explorer, Submit, SoftwareLinker,
  MayaLauncher, or a new one) → touch only its own
  `plugins/core/<Name>/`, `plugins/repo_internal/<Name>/`, or
  `cache/plugins/<Name>/` folder. See the `ukorehub-plugin` skill and
  `plugins/README.md` — never
  open a sibling plugin's source, and cross-plugin data/UI coordination
  goes through the documented
  `plugin_config_store`/`UICommandService` conventions, not imports.
- Told to fix/change `core/` → touch only `core/` unless the change
  requires updating an `interface/` call site.
- Told to fix/change `interface/` → touch only `interface/` unless the
  change requires a `core/` addition it depends on. Note Explorer/Submit
  are `plugins/`, not `interface/`, despite showing up as ordinary tabs —
  see the plugin bullet above instead.

## Testing — only when explicitly requested

Do not run `pytest`, headless smoke-test scripts, or import-sweep checks
after a change unless the user explicitly asks for testing/verification in
that turn. Skipping this step makes iteration noticeably faster, and the
user will ask for it by name when they want it. This applies even to
changes that would normally warrant self-verification (UI rewiring,
renamed modules, registry changes) — implement the change, report what
changed, and stop there.

## Headless/smoke testing — never point at real `data/`/`cache/`

If you need to construct real app objects (`MetadataStore`, `LocalConfigStore`,
`MainWindow`, etc.) outside of `pytest` — e.g. a throwaway headless
smoke-test script to verify wiring after a registry/constructor change —
**never point them at the repo's real `data/`/`cache/` directories or the
real `REPO_ROOT`**. Copy them into a scratch/tmp directory first and
construct everything against that copy instead. `cache/local_config.json`
can have a real `active_repo_id` saved, which makes `MainWindow.__init__` kick off a
real background git sync (`MainWindow._start_auto_sync`, delegating to
`plugins/core/submit/repo_git_status_page.py`'s
`RepoGitStatusPage.sync_active_repo`) on a background `QThread` that starts
running the moment `.start()` is called, independent of whether
`app.exec()` ever runs. A real UkoreHub.exe /
`launcher.py` instance may also be running concurrently on the studio
machine you're working on — check for one (e.g. `tasklist`) before assuming
any change to a shared JSON store is safe to discard or revert.
`pytest`'s own tests are unaffected by this — they already use `tmp_path`.

## Program folder stays program-only — user/project data never lives under REPO_ROOT

`cache/` and `storage/` (see their entries below) are per-machine, per-user
data — never something the installed app folder should own. UkoreHub.exe
(UkoreHubLauncher repo) normally points the `UKOREHUB_CACHE_DIR` /
`UKOREHUB_STORAGE_DIR` env vars outside `REPO_ROOT` before spawning
`launcher.py`. When those aren't set — the `python launcher.py` direct
dev-invocation path, which bypasses UkoreHub.exe entirely — `launcher.py`
falls back to `~/Documents/UkoreHub/cache` and `~/Documents/UkoreHub/storage`
(`USER_DATA_DIR` in `launcher.py`), **not** `REPO_ROOT/cache` /
`REPO_ROOT/storage`. Changed 2026-08-09: the app folder must contain only
the program itself, so Update can wipe/replace it wholesale (see
UkoreHubLauncher's README.md) without risking or silently orphaning real
user/project data next to the new copy. Never reintroduce a
`REPO_ROOT`-relative default for either path — any new per-machine or
per-user data directory added later must default outside `REPO_ROOT` the
same way, not join `cache/`/`storage/` as a sibling under the app folder.

## Project layout

- `core/` — non-UI logic: metadata store, git operations, GitHub auth, theming.
- `interface/` — PySide6 GUI: sidebar, pages, dialogs, background workers.
- `data/` — cloud-synced JSON blob caches only (`projects.json` — an index,
  real payload in `projects/<id>.json` per project, each with its own
  Program Database — `system_config.json`, `plugins/core/*.json`, and a
  retired `programs.json`, see `data/README.md`), no exceptions — several
  Maya-side scripts under `plugins/repo_internal/` hardcode these exact
  `data/` paths directly (they can't import `PluginAPI`), so nothing else
  belongs here. See [data/README.md](data/README.md) — don't open these
  unless the task needs a concrete current value.
- `assets/` — git-tracked binary images (`thumbnails/`, `program_icons/`,
  `browser_link_icons/`, `icons/`), never cloud-synced. See
  [assets/README.md](assets/README.md) — never open an image file in here.
- `appdata/` — static git-tracked bootstrap defaults/examples
  (`system_config.default.json`, `projects.example.json`), never
  cloud-synced and never written by the running app. See
  [appdata/README.md](appdata/README.md).
- `plugins/` — UkoreHub's own sub-systems: `plugins/core/` (bundled,
  on-by-default, opt-out per repo) and `plugins/repo_internal/` (bundled,
  off-by-default, opt-in per repo). See `core/extensibility/README.md` for
  the discovery mechanism and `plugins/README.md` plus the `ukorehub-plugin`
  skill for the "stay inside one folder" editing discipline it uses.
- `cache/` — every per-machine, gitignored file UkoreHub owns (actual
  on-disk location is `CACHE_DIR`, set by `launcher.py` — see "Program
  folder stays program-only" above, **not** necessarily under `REPO_ROOT`):
  `local_config.json`, `github_token.json` (a credential — never open,
  quote, or otherwise surface its contents),
  `plugin_local_config/`, and `plugins/` — **repo plugins**: each entry is
  its own separate git clone (own remote/history, not part of this repo at
  all), fetched/updated on demand only for a repo that requires it. Never
  read or list files under `cache/` unless the task explicitly needs to
  (e.g. names a repo plugin by folder name) — same reasoning as `storage/`
  below, this is fetched/generated/runtime content, not something to
  explore speculatively (though unlike `storage/`, a `cache/plugins/`
  entry's plugin.py/manifest.json are real code worth reading when a task
  is actually about that specific plugin — see `plugins/README.md`). See
  [cache/README.md](cache/README.md) for the full breakdown.
- `storage/` — **the actual workspace root**, pointed to by
  `cache/local_config.json`'s `workspace_root` (actual on-disk location is
  `STORAGE_DIR`, set by `launcher.py` — see "Program folder stays
  program-only" above, **not** necessarily under `REPO_ROOT`): real cloned
  production repos
  (Maya/Blender scenes, huge binaries, studio artwork), gitignored. Named
  `storage/`, not `projects/`, specifically so it can't be confused with
  `data/projects/` (the per-project metadata blobs — see
  [data/README.md](data/README.md)). **Never read or list files under here
  unless the user explicitly asks** — there is no code in it, it can be
  enormous, and its contents are production data, not something to explore
  speculatively.
- `launcher.py` — entry point.
- `developer/tests/` — pytest suite (`pytest.ini` at repo root points
  `testpaths` here). Not published to `main` — see `developer/README.md`.
