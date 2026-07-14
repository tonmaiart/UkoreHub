# interface/

PySide6 GUI layer for UkoreHub. Builds on `core/` for all data and git
operations — widgets here handle layout, user interaction, and background
`QThread` workers so the UI doesn't block on git/network calls.

Organized by window/tab rather than by suffix convention: each of
`sidebar/`, `login/`, `explorer/`, `submit/`, `about/`, `settings/` owns
one area of the app end-to-end (page + its dialogs + its workers).
`shared/` holds the handful of files genuinely used by 2+ of those folders
(checked repo-wide before this split — see `shared/README.md`). Everything
left flat at this level is app-wiring/registries with no single window
home — `main_window.py` is the one file that threads all of it together.

**Working here:** read that window's own `README.md` first — it's a
faster map than opening every file. Stay inside the one folder the task
names; only cross into `shared/` or a root-level registry when the task
genuinely needs it (e.g. a new page that needs a new `shared/` helper, or
a new top-level section that needs `section_registry.py`).

## Root-level app shell (no single window)

- `main_window.py` — top-level `QMainWindow`: constructs every window's
  page from `SectionRegistry`, wires `sidebar/`'s `Sidebar` (the left-hand
  navigation column — thumbnail/repo picker, `SectionTabList`, GitHub
  login/Update/sync footer), drives active-repo restore + auto-sync on
  launch, and owns the one shared `QWebEngineProfile`
  (`web_engine_profile.py`) every `about/browser_link_page.py` tab uses.
  Every section is its own standalone page in `view_stack`, switched to via
  `Sidebar.navigation_changed`.
- `section_registry.py` / `settings_tab_registry.py` — open, ordered
  registries that top-level sections and Settings tabs register into
  (built-in and plugin-provided alike). `repo_addon_panel_registry.py` is
  a third, simpler one — a plain `addon_id -> panel_factory` lookup,
  consumed by `about/repo_about_page.py`'s dynamic per-add-on sub-tabs.
  All three stay at this root level rather than moving into a window
  folder because they're cross-cutting infrastructure with no single
  window — and `settings_tab_registry.py` specifically is imported
  directly by an external add-on (`plugins/studio/software_linker/plugin.py`),
  so keeping it at a stable path avoids touching that add-on's source.
- `builtin_sections.py` / `builtin_settings_tabs.py` — construct the
  built-in pages/tabs (pulling from `explorer/`, `submit/`, `about/`,
  `settings/`) and register them into the registries above, exactly as a
  plugin would register its own.
- `plugin_api.py` — `PluginAPI`, the object passed to every plugin's/
  add-on's `register(api)` entry point; composes `core/` services with the
  section/settings-tab/repo-addon-panel registries.
- `web_engine_profile.py` — `make_persistent_browser_link_profile`, the
  single disk-backed `QWebEngineProfile` `main_window.py` constructs once
  so every Browser Link tab's login survives app restarts.
- `theme_apply.py` — applies a `core.theme` stylesheet to the
  `QApplication`; used only by `launcher.py`.

## Window folders

- `sidebar/` — the left navigation column: `ActiveRepoWidget` (repo
  thumbnail banner with the repo name overlaid + a "Project / Repo" picker
  button), `SectionTabList` (a vertical list of section tabs + dynamic
  Browser Link tabs + a trailing Setting row), and a footer with sync
  progress, the Update button, and GitHub login/logout. See
  `sidebar/README.md`.
- `login/` — the mandatory GitHub login gate and OAuth device-flow dialog,
  plus the repo picker. See `login/README.md`.
- `explorer/` — Explorer tab: file browser, Folder Navigator, Recent
  Files + Favorites sidebar, per-path commit history. See
  `explorer/README.md`.
- `submit/` — Submit tab: stage/unstage/revert, commit → pull → (resolve
  conflicts) → push, whole-repo commit log. See `submit/README.md`.
- `about/` — About tab: repo info, requirements/add-ons, Browser Links,
  and the dynamic per-add-on panels, plus the Browser Link tab template
  itself. See `about/README.md`.
- `settings/` — the Setting view's tabs: common settings, program
  database, project data editor, project sync status, plugin catalog,
  add-on settings. See `settings/README.md`.
- `shared/` — `commit_history.py` (Explorer + Submit), `dialogs.py`
  (Settings + About), `project_repo_tree.py` (login's repo picker +
  Settings) — files with a confirmed multi-window consumer. See
  `shared/README.md`.

## Testing conventions

Qt widgets are **never constructed inside pytest tests**: registries are
tested with `page_factory=lambda: None`, verifying registry bookkeeping
only (registration, duplicate-key rejection, lookup/ordering), never
`QWidget` behavior. For anything that genuinely needs a live `QApplication`
+ `MainWindow` (e.g. verifying a new registry threads all the way through
without crashing), use a throwaway headless smoke-test script instead of a
pytest test — **and always point it at a scratch copy of `data/`, never
the real one** (see root `CLAUDE.md`'s "Headless/smoke testing" section):
construct `QApplication`, all registries, and `MainWindow` without calling
`app.exec()`, `patch.object` any dialog-showing methods
(`_show_launch_dialog`, `_check_for_update`) to no-ops, and end with
`sys.stdout.flush(); os._exit(0)` — `os._exit` is required because Qt/
Windows can hang on normal process teardown after `QApplication` is
destroyed without an explicit `app.quit()`; without the `os._exit(0)` the
script can look hung even though it actually finished. Note that
constructing a real `QWebEngineProfile`/`QWebEngineView` can itself be slow
to spin up cold (Chromium subsystem init) — a plain
`importlib.import_module` sweep over every file is a faster, sufficient
check for import-path correctness alone (no GUI needed).
