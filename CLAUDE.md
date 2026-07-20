# UkoreHub

Pipeline tool to launch/sync projects in Ukore Studio — a Git repo launcher
built on PySide6. See [README.md](README.md) for the full project overview,
prerequisites, and config split (system vs. local).

**Before acting on a casual/colloquial term the user uses for a feature**
(e.g. "the program's setting", "Viewgraph", "Custom Path") **or before
asking a clarifying question about one, read [GLOSSARY.md](GLOSSARY.md)
first** — it maps terms that are easy to misread onto the actual feature/
file, recorded specifically because one of these got misread once already
(see its own entries for the incidents). If a term isn't in there and the
mapping is genuinely ambiguous, ask the user rather than guessing — and
add the resolved mapping to `GLOSSARY.md` afterward so it doesn't need
asking again.

**Before changing code in a file or area listed in
[bug-history/README.md](bug-history/README.md)'s index, read that entry
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
folder (a new `add-on/<Name>/`, a new subfolder under `core/` or
`interface/`), add a short `README.md` to it in the same style as the
existing ones (see `core/README.md` for the reference tone/format — a
short intro paragraph, then a flat bullet list of what each file/subfolder
does and how they relate).

## Scoped editing — stay inside the folder the task names

When a task is about one specific area — a single `add-on/<Name>/`, a
single `plugins/studio/<Name>/` or `plugins/local/<Name>/`, `core/`, or
`interface/` — read and edit only that folder. Don't open sibling folders
"just in case" unless the task genuinely crosses the boundary (e.g. a
`core/` change whose call sites in `interface/` also need updating).
Concretely:
- Told to fix/change an add-on → touch only `add-on/<Name>/`. See the
  `ukorehub-addon` skill and `add-on/README.md` for why sibling add-ons
  especially shouldn't be opened, and how cross-add-on data sharing works
  without reading another add-on's source.
- Told to fix/change a plugin (Explorer, Submit, SoftwareLinker,
  MayaLauncher, or a new one) → touch only its own
  `plugins/studio/<Name>/`/`plugins/local/<Name>/`
  folder. See the `ukorehub-plugin` skill and `plugins/README.md` for the
  same discipline as add-ons — never open a sibling plugin's source, and
  cross-plugin data/UI coordination goes through the documented
  `plugin_config_store`/`SectionHost` conventions, not imports.
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

## Headless/smoke testing — never point at real `data/`

If you need to construct real app objects (`MetadataStore`, `LocalConfigStore`,
`MainWindow`, etc.) outside of `pytest` — e.g. a throwaway headless
smoke-test script to verify wiring after a registry/constructor change —
**never point them at the repo's real `data/` directory or the real
`REPO_ROOT`**. Copy `data/` into a scratch/tmp directory first and construct
everything against that copy instead. `data/local_config.json` can have a
real `active_repo_id` saved, which makes `MainWindow.__init__` kick off a
real background git sync (`MainWindow._start_auto_sync`, delegating to
`plugins/studio/submit/repo_git_status_page.py`'s
`RepoGitStatusPage.sync_active_repo`) on a background `QThread` that starts
running the moment `.start()` is called, independent of whether
`app.exec()` ever runs. A real UkoreHub.exe /
`launcher.py` instance may also be running concurrently on the studio
machine you're working on — check for one (e.g. `tasklist`) before assuming
any change to a shared JSON store is safe to discard or revert.
`pytest`'s own tests are unaffected by this — they already use `tmp_path`.

## Project layout

- `core/` — non-UI logic: metadata store, git operations, GitHub auth, theming.
- `interface/` — PySide6 GUI: sidebar, pages, dialogs, background workers.
- `data/` — tracked shared config (`projects.json`, `programs.json`,
  thumbnails/icons) plus gitignored per-machine config. See
  [data/README.md](data/README.md) — don't open the JSON stores unless the
  task needs a concrete current value, and never open the image
  directories (`thumbnails/`, `program_icons/`, `addon_icons/`) at all.
- `plugins/` vs `add-on/` — Plugins are UkoreHub's own always-on sub-systems
  (every project, never toggled); Add-ons are per-repo opt-in extensions
  (`Repo.enabled_addon_ids`, shared team data). Different concepts — see
  `core/extensibility/README.md` before touching either, and see
  `plugins/README.md`/`add-on/README.md` plus the `ukorehub-plugin`/
  `ukorehub-addon` skills for the "stay inside one folder" editing
  discipline each uses.
- `projects/` — **the actual workspace root**, pointed to by
  `data/local_config.json`'s `workspace_root`: real cloned production repos
  (Maya/Blender scenes, huge binaries, studio artwork), gitignored. **Never
  read or list files under here unless the user explicitly asks** — there
  is no code in it, it can be enormous, and its contents are production
  data, not something to explore speculatively.
- `launcher.py` — entry point.
- `tests/` — pytest suite (`pytest.ini` at repo root).
