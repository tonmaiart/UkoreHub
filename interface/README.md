# interface/

PySide6 GUI layer for UkoreHub. Builds on `core/` for all data and git
operations — widgets here handle layout, user interaction, and background
`QThread` workers so the UI doesn't block on git/network calls.

Organized by window/tab rather than by suffix convention: each of
`sidebar/`, `login/`, `about/`, `settings/` owns one area of the app
end-to-end (page + its dialogs + its workers). Explorer and Submit used to
live here too (`explorer/`, `submit/`) but are now real always-on plugins
under `plugins/studio/explorer/` and `plugins/studio/submit/` — registered
into `SectionRegistry` via `register(api)` exactly like any other plugin,
not special-cased by `interface/` — see their own `README.md`s and
`core/extensibility/README.md` for the plugins-vs-add-ons distinction.
`shared/` holds the handful of files genuinely used by 2+ consumers,
`interface/` windows and those two plugins alike (checked repo-wide before
this split — see `shared/README.md`). Everything left flat at this level is
app-wiring/registries with no single window home — `main_window.py` is the
one file that threads all of it together.

**Working here:** read that window's own `README.md` first — it's a
faster map than opening every file. Stay inside the one folder the task
names; only cross into `shared/` or a root-level registry when the task
genuinely needs it (e.g. a new page that needs a new `shared/` helper, or
a new top-level section that needs `section_registry.py`).

## Root-level app shell (no single window)

- `main_window.py` — top-level `QMainWindow`: constructs every window's
  page from `SectionRegistry`, wires `sidebar/`'s `Sidebar` (the left-hand
  navigation column — display-only repo thumbnail/name label,
  `SectionTabList`, GitHub login/Update/sync footer), drives active-repo
  restore + auto-sync on launch, and owns the one shared `QWebEngineProfile`
  (`web_engine_profile.py`) every `about/browser_link_page.py` tab uses.
  Every ordinary section is its own standalone page in `view_stack`,
  switched to via `Sidebar.navigation_changed` — except a section flagged
  `SectionSpec.persistent=True` (Project Editor), which is never added to
  `view_stack`/`SectionTabList` at all and instead sits permanently docked
  beside `view_stack` in a `QSplitter`, always visible regardless of which
  ordinary section is currently showing.
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
  built-in pages/tabs (pulling from `about/`, `settings/` — Explorer and
  Submit register themselves from `plugins/studio/`, not from here) and
  register them into the registries above, exactly as a plugin would
  register its own.
- `plugin_api.py` — `PluginAPI`, the object passed to every plugin's/
  add-on's `register(api)` entry point; composes `core/` services with the
  section/settings-tab/repo-addon-panel registries.
- `web_engine_profile.py` — `make_persistent_browser_link_profile`, the
  single disk-backed `QWebEngineProfile` `main_window.py` constructs once
  so every Browser Link tab's login survives app restarts.
- `theme_apply.py` — applies a `core.theme` stylesheet to the
  `QApplication`; used only by `launcher.py`.

## Window folders

- `sidebar/` — the left navigation column: `ActiveRepoWidget` (display-only
  repo thumbnail + name label — no click-to-open picker; double-clicking a
  node in Project Editor's always-visible graph panel is the only way to
  change the active repo now), `SectionTabList` (a vertical list of section
  tabs + dynamic Browser Link tabs + a trailing Setting row — Project
  Editor is not one of these rows, see below), and a footer with sync
  progress, the Update button, and GitHub login/logout. See
  `sidebar/README.md`.
- `login/` — the mandatory GitHub login gate (drawn as an overlay on top of
  `main_window.py`'s own content, not a popup), the OAuth device-flow
  dialog, and the repo picker. See `login/README.md`.
- `about/` — About tab: repo info, requirements/add-ons, Browser Links,
  and the dynamic per-add-on panels, plus the Browser Link tab template
  itself. See `about/README.md`.
- `settings/` — the Setting view's tabs: common settings, program
  database, project data editor, project sync status, plugin catalog,
  add-on settings. See `settings/README.md`.
- `shared/` — `commit_history.py` (`plugins/studio/explorer/` +
  `plugins/studio/submit/`), `dialogs.py` (Settings + About),
  `project_repo_tree.py` (login's repo picker + Settings) — files with a
  confirmed multi-consumer use. See `shared/README.md`.

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
`app.exec()`. Pre-seed the scratch `local_config_store` with a fake
`github_username` and a fake token in the scratch `token_store` before
constructing `MainWindow`, so it skips `LoginOverlay` entirely (that path
is otherwise indistinguishable from a real hang since it just sits there
waiting for a click); also `patch.object` `_check_for_update` to a no-op,
and end with
`sys.stdout.flush(); os._exit(0)` — `os._exit` is required because Qt/
Windows can hang on normal process teardown after `QApplication` is
destroyed without an explicit `app.quit()`; without the `os._exit(0)` the
script can look hung even though it actually finished. Note that
constructing a real `QWebEngineProfile`/`QWebEngineView` can itself be slow
to spin up cold (Chromium subsystem init) — a plain
`importlib.import_module` sweep over every file is a faster, sufficient
check for import-path correctness alone (no GUI needed).
