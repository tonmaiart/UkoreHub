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
context. Not every folder has one; skip this step where it's absent.

## Project layout

- `core/` — non-UI logic: metadata store, git operations, GitHub auth, theming.
- `interface/` — PySide6 GUI: sidebar, pages, dialogs, background workers.
- `data/` — tracked shared config (`projects.json`, `programs.json`,
  thumbnails/icons) plus gitignored per-machine config.
- `plugins/` vs `add-on/` — Plugins are UkoreHub's own always-on sub-systems
  (every project, never toggled); Add-ons are per-repo opt-in extensions
  (`Repo.enabled_addon_ids`, shared team data). Different concepts — see
  `core/extensibility/README.md` before touching either.
- `launcher.py` — entry point.
- `tests/` — pytest suite (`pytest.ini` at repo root).
