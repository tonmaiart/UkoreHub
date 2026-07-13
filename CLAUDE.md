# UkoreHub

Pipeline tool to launch/sync projects in Ukore Studio — a Git repo launcher
built on PySide6. See [README.md](README.md) for the full project overview,
prerequisites, and config split (system vs. local).

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

When a task is about one specific area — a single `add-on/<Name>/`,
`core/`, or `interface/` — read and edit only that folder. Don't open
sibling folders "just in case" unless the task genuinely crosses the
boundary (e.g. a `core/` change whose call sites in `interface/` also need
updating). Concretely:
- Told to fix/change an add-on → touch only `add-on/<Name>/`. See the
  `ukorehub-addon` skill and `add-on/README.md` for why sibling add-ons
  especially shouldn't be opened, and how cross-add-on data sharing works
  without reading another add-on's source.
- Told to fix/change `core/` → touch only `core/` unless the change
  requires updating an `interface/` call site.
- Told to fix/change `interface/` → touch only `interface/` unless the
  change requires a `core/` addition it depends on.

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
  `core/extensibility/README.md` before touching either.
- `projects/` — **the actual workspace root**, pointed to by
  `data/local_config.json`'s `workspace_root`: real cloned production repos
  (Maya/Blender scenes, huge binaries, studio artwork), gitignored. **Never
  read or list files under here unless the user explicitly asks** — there
  is no code in it, it can be enormous, and its contents are production
  data, not something to explore speculatively.
- `launcher.py` — entry point.
- `tests/` — pytest suite (`pytest.ini` at repo root).
