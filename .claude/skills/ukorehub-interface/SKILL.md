---
name: ukorehub-interface
description: Reference for UkoreHub's interface/ layer (C:\Tonmai\UkoreHub) — the PySide6 GUI, organized by window (sidebar/, login/, explorer/, submit/, about/, settings/, plus a shared/ for multi-window files): MainWindow's left-hand Sidebar / SectionTabList navigation, the four extension registries (SectionRegistry, SettingsTabRegistry, RepoAddonPanelRegistry, FileOpenerRegistry), PluginAPI composition, and the builtin_*.py dogfooding pattern. Use this whenever adding a page, a settings tab, a top-level section, a Repo Add-on panel, or any UI-facing plugin/add-on registration — or whenever the task touches interface/main_window.py, any interface/<window>/ folder, interface/plugin_api.py, or any interface/*_registry.py, even if the user doesn't say "interface" explicitly (e.g. "add a settings page", "show this as its own tab").
---

# UkoreHub interface/ — architecture reference

`interface/` is the PySide6 GUI layer sitting on top of the Qt-free `core/`
(see the `ukorehub-core` skill for that side). Read `interface/README.md`
first for the current file listing — this skill is the architecture and the
*why*, kept deliberately shorter than a file index.

## Scoped editing

A task about `interface/` stays inside `interface/` — don't open `core/` or
`add-on/` files unless the change genuinely needs a new `core/` primitive
to build on. `interface/` is organized by window, not by suffix convention:
`sidebar/`, `login/`, `explorer/`, `submit/`, `about/`, `settings/` each
own one area of the app end-to-end (page + its own dialogs + its own
workers) — a task about one window opens only that folder, plus
`main_window.py` or the relevant root-level `*_registry.py` only if the
task is about wiring, not page content. `shared/` holds the handful of
files with a confirmed multi-window consumer (`commit_history.py`,
`dialogs.py`, `project_repo_tree.py`) — a change there affects every window
that imports it, listed in `shared/README.md`, so check all of them.

## MainWindow structure — left Sidebar, no modal Settings dialog

`interface/main_window.py`'s `MainWindow` no longer opens a modal
`QDialog` for settings (that was ripped out in favor of an embedded tab
switcher). Navigation lives in a persistent left-hand column rather than a
top row (an earlier iteration of this redesign tried a horizontal top
MenuBar — that was superseded by this Sidebar). Current structure, left to
right:

- **`Sidebar`** (`interface/sidebar/sidebar.py`, fixed-width left column).
  Top to bottom within it:
  - **`ActiveRepoWidget`** (`interface/sidebar/active_repo_widget.py`): a
    fill-cropped (never rounded) repo thumbnail banner with a plain name
    label beneath it. Display-only as of 2026-07-15 — no click-to-open
    picker anymore (that button existed, was removed, then this display-
    only version was re-added the same day at the user's request);
    clicking a repo node in Project Editor's `QGraphicsView` graph
    (`plugins/studio/project_editor/`) is the only way to change the
    active repo now, via `SectionHost.set_active_repo` (see below) — a
    single click, not a double-click (changed the same day too; a
    not-yet-cloned repo gets a one-time confirmation first).
    `MainWindow` pushes into it directly from `_restore_active_repo`/
    `_set_active_repo`/`_on_repo_thumbnail_changed`.
  - **`SectionTabList`** (`interface/sidebar/section_tab_list.py`, a
    vertical `QListWidget`, stretched to fill the remaining height): one
    row per `SectionRegistry` section **excluding** any
    `SectionSpec.persistent=True` section (currently Explorer/Submit/About,
    in registry order — Project Editor is `persistent=True` so it never
    gets a row here, see below), then one row per dynamic Browser Link on
    the active repo (inserted right after the fixed sections, rebuilt on
    every repo switch), then a final **Setting** row (`SETTINGS_KEY`) that
    always stays last. Because this is one single-selection list rather
    than two independent `QButtonGroup`s (the old MenuBar's design), there
    is nothing to keep in sync by hand anymore — `SectionTabList` emits one
    `navigation_changed(key)` signal for every row, Setting included.
  - A **footer** (`sidebarFooter`) with sync status, the Update button,
    and GitHub login/logout (`interface/login/github_auth_widget.py`).
- **A view stack** (`MainWindow.view_stack`) with one full-width top-level
  page per **non-persistent** `SectionRegistry` section (Explorer/Submit/
  About — every section is standalone, there's no shared sidebar-backed
  container), one page per dynamic Browser Link tab, plus the **settings
  view** (`SettingsTabRegistry`-driven, shown when the Setting row is
  selected — as of 2026-07-15 it only renders `CATEGORY_GENERAL`/
  `CATEGORY_DEVELOPER`; every `CATEGORY_REPO` tab now renders generically
  inside a "Repository Setting..." popup opened from a Project Editor
  node's right-click menu instead, see that plugin's README).
  `Sidebar.navigation_changed` picks a page by key via
  `MainWindow._on_navigation_changed`, which special-cases
  `key == SETTINGS_KEY` to show the settings view instead of looking it up
  in `_section_view_index`/`_dynamic_view_index`. There is no "Repo"/Project
  Info section anymore — it was removed; its "Repo Add-on" sub-tab's job
  (showing each enabled add-on's per-repo panel via `RepoAddonPanelRegistry`)
  moved into a "Repo About" section next. That section was itself removed
  2026-07-20 (no longer needed) — `RepoAddonPanelRegistry` currently has no
  UI consumer at all; a panel registered via `api.register_repo_addon_panel`
  is stored but never rendered anywhere.
- **Persistent sections** (`SectionSpec.persistent=True`, currently only
  Project Editor): never a `SectionTabList` row, never added to `view_stack`
  at all — instead `MainWindow._build_main_ui` docks it permanently beside
  `view_stack` inside a `QSplitter` (`content_splitter`, initial sizes
  `[1000, 420]` favoring `view_stack`, user-resizable), so it stays visible
  regardless of which ordinary section is currently showing. Since it's
  never `view_stack.currentWidget()`, `MainWindow._apply_to_current_page()`
  never reaches it — `_apply_to_persistent_pages()` pushes `set_repo(...)`
  to every persistent page directly instead, called alongside
  `_apply_to_current_page()` wherever the active repo actually changes
  (login restore, relogin, `_set_active_repo` — deliberately **not** on
  every plain navigation switch in `_on_navigation_changed`, since a
  persistent page's content doesn't depend on which ordinary section is
  showing). `SectionSpec.wire`/`background_threads`/`page_factory` all
  still apply identically to a persistent section — only its Sidebar row
  and `view_stack` membership are skipped.
- Every settings page **self-persists on every change** — there is no
  Save/Cancel step anywhere. `SettingsTabSpec` has no `on_save`/`on_cancel`
  hooks; if you're writing a new settings page, write directly through
  whatever store you're editing the moment the user changes a value, the
  same way every existing settings page does.

## The four registries

All live under `interface/`, except `FileOpenerRegistry` which is Qt-free
and therefore lives in `core/extensibility/` (see `ukorehub-core` skill) —
don't go looking for it here, even though it's UI-adjacent in purpose.

| Registry | Spec dataclass | Keyed? | Purpose |
|---|---|---|---|
| `SectionRegistry` | `SectionSpec` | yes, rejects dup keys | Top-level sections, rendered as rows in Sidebar's `SectionTabList` (Explorer, Submit, ...) — unless `persistent=True` (Project Editor), which docks permanently beside `view_stack` instead of getting a row |
| `SettingsTabRegistry` | `SettingsTabSpec` | yes | Tabs shown in the "Setting" view |
| `RepoAddonPanelRegistry` | (factory keyed by addon_id) | yes | Per-add-on per-repo panel — currently has no UI consumer (its only renderer, Repo About, was removed 2026-07-20); a registered panel is stored but never displayed |
| `FileOpenerRegistry` | `FileOpenerSpec` | **no**, plain list, first-match-wins | Add-on can claim responsibility for opening a file extension (lives in `core/`) |

Every registered page/tab factory follows the same **`page_factory: Callable[[], QWidget]`** convention — no arguments, construct-on-demand. This is also why pytest can smoke-test registries without ever instantiating a real `QWidget`: tests register `page_factory=lambda: None` and only assert on registry bookkeeping (duplicate-key rejection, ordering), never call the factory. `RepoAddonPanelRegistry`'s `panel_factory` is the one exception — it takes the active `Repo` directly (`Callable[[Repo], QWidget]`), for whatever future consumer rebuilds these panels fresh on every repo switch rather than constructing once.

Built-ins register into the exact same registries a plugin/add-on would —
`interface/builtin_settings_tabs.py` calls
the same `register_*`/`api.register_*` surface as
`plugins/studio/maya_launcher/plugin.py` does. This "dogfooding" is deliberate: if a
built-in page needs something the registry API can't express, that's a
signal the registry API itself is incomplete — don't special-case
built-ins with a side channel.

## `interface/plugin_api.py` — `PluginAPI`

The single object passed to every plugin's/add-on's `register(api)`. It's a
pure composition/facade over already-constructed services — it does not
construct anything itself, everything is handed in via `launcher.py`.
Current constructor:

```python
def __init__(self, *, store, program_store, local_config_store, git_service, hooks,
             section_registry, settings_tab_registry,
             repo_addon_panel_registry, file_opener_registry, plugins_data_dir, app_root):
```

Notable surface:
- `api.programs` → wraps `program_store` (`get_program(id)` raises
  `core.exceptions.NotFoundError`, not `None`/`KeyError` — catch that
  specifically).
- `api.plugin_config_store(plugin_id, shared: bool)` → returns a
  `PluginConfigStore` namespaced to `plugin_id`. `shared=True` writes under
  the git-tracked studio config dir, `shared=False` under the gitignored
  local one. Two unrelated plugins agreeing on the same `plugin_id` string
  share the same file — see `plugins/studio/maya_launcher/plugin.py`
  reading `plugins/studio/software_linker`'s config for the live example
  (`plugins/README.md`'s "Sharing data with another plugin" section for
  the general write-up).
- `api.app_root` → `Path` to the UkoreHub install root itself (i.e.
  `launcher.py`'s own `REPO_ROOT`), for a plugin/add-on that needs to
  reference other paths inside the UkoreHub installation (like
  `plugins/studio/UkoreBrowser/plugin.py` contributing `api.app_root`
  itself onto `PYTHONPATH` so its vendored Maya-side code can
  `import core.store`) without guessing paths from `__file__`.
- `api.register_repo_addon_panel(addon_id, panel_factory)` — shows up as
  its own sub-tab (named after the add-on's manifest) inside the About
  page's left tab bar, for any repo that has that add-on enabled. Only
  meaningful for a genuine repo-scoped `add-on/` (gated by
  `Repo.enabled_addon_ids`) — an always-on `plugins/` entry generally
  shouldn't use this (see `plugins/studio/maya_launcher/README.md` for why
  it dropped this in favor of its own Settings tab instead).
- `api.register_file_opener(addon_id, extensions, opener)`,
  `api.register_section(...)`, `api.register_settings_tab(...)` — one
  register method per remaining registry above.
- `api.settings_tab_registry` → read access to the same `SettingsTabRegistry`
  `register_settings_tab()` writes into, added 2026-07-15 for
  `plugins/studio/project_editor/`'s right panel, which enumerates every
  `CATEGORY_REPO` spec generically and renders it as a collapsible section
  rather than contributing a tab of its own — same read-access-alongside-
  write-method shape as `api.file_opener_registry` above.

## Page protocol: `set_repo()`

Most pages that need to react to the active repo changing (Repo Browser,
Repo Git Status) implement a
`set_repo(repo: Repo | None) -> None` method, called by `MainWindow`
whenever the active repo or the visible top-level tab changes. If you're
adding a new page that cares which repo is active, implement this method
rather than inventing a new callback — it's how every existing page stays
in sync.

## File-open flow — where an add-on actually intercepts a double-click

This is the one flow worth tracing end-to-end since it crosses several
files and the naming ("open") appears at every layer:

1. `plugins/studio/explorer/browser_widget.py`'s `RepoBrowserWidget` takes an
   `open_file: Callable[[Path], None] | None = None` constructor param
   (default `None` falls back to `core.os_utils.open_with_default_app`,
   i.e. the OS file association / `os.startfile`). Double-clicking a row
   calls `self._open_file(path)`, then unconditionally emits
   `file_opened.emit(path)` regardless of which opener handled it.
2. `plugins/studio/explorer/repo_browser_page.py`'s `RepoBrowserPage` constructs
   `RepoBrowserWidget(..., open_file=self._open_file)` and implements:
   ```python
   def _open_file(self, path: Path) -> None:
       if self._active_repo is not None:
           opener = self._file_opener_registry.find_opener(path, self._active_repo.enabled_addon_ids)
           if opener is not None and opener(path, self._active_repo):
               return
       open_with_default_app(path)
   ```
   Note it tracks `self._active_repo` as the **full `Repo` object** (not
   just an id string) precisely so it can read `.enabled_addon_ids` here.
3. `FileOpenerRegistry.find_opener(path, enabled_addon_ids)` only returns a
   match if the extension matches *and* the registering add-on's id is in
   the repo's `enabled_addon_ids` — the registry has no notion of "current
   repo" itself, that gating is entirely the caller's responsibility.

If you add a new file-open entry point, replicate this same
check-registry-then-fallback shape rather than calling
`open_with_default_app` directly, so add-on-provided openers stay
consistent everywhere a file can be opened from. (Explorer used to also
have Recent Files and Favorites lists that navigated but never opened a
file — both were removed entirely for a cleaner Explorer tab; double-click
in the file table is the only file-open entry point there now.)

## Wiring: `launcher.py`

`launcher.py` is where every registry, store, and `PluginAPI` gets
constructed and threaded together — it's the single place that knows the
full dependency graph. When adding a new registry or constructor param
anywhere in this chain, `launcher.py` is always one of the files you touch:
it constructs the registry, passes it into `register_builtin_*(...)`, into
`PluginAPI(...)`, and into `MainWindow(...)`.

## Testing conventions

Same as `core/` (see `ukorehub-core` skill) — real `tmp_path`, no mocking.
Qt widgets are **never constructed inside pytest tests**: registries are
tested with `page_factory=lambda: None`, verifying registry bookkeeping
only (registration, duplicate-key rejection, lookup/ordering), never
`QWidget` behavior. For anything that genuinely needs a live `QApplication`
+ `MainWindow` (e.g. verifying a new registry threads all the way through
without crashing), use a throwaway headless smoke-test script instead of a
pytest test — **and always point it at a scratch copy of `data/`, never
the real `data/` or `REPO_ROOT`** (see root `CLAUDE.md`'s "Headless/smoke
testing" section — `MainWindow.__init__` can kick off a real background
git sync/pull against whatever it's pointed at the moment a `QThread`
worker's `.start()` is called, independent of whether `app.exec()` ever
runs, and a real UkoreHub.exe may already be running concurrently):
construct `QApplication`, all registries, and `MainWindow` without calling
`app.exec()`. Pre-seed the scratch `local_config_store` with a fake
`github_username` and a fake token in the scratch `token_store` before
constructing `MainWindow`, so it skips drawing `LoginOverlay` entirely
(that path otherwise just sits there waiting for a click, indistinguishable
from a real hang); also `patch.object` `_check_for_update` to a no-op, and
end with
`sys.stdout.flush(); os._exit(0)` — `os._exit` is required because Qt/
Windows can hang on normal process teardown after `QApplication` is
destroyed without an explicit `app.quit()`; without the `os._exit(0)` the
script can look hung even though it actually finished. Note that
constructing a real `QWebEngineProfile`/`QWebEngineView`
(`web_engine_profile.py`, `about/browser_link_page.py`) can itself be slow
to spin up cold (Chromium subsystem init) and can hang a headless script
before it ever reaches `MainWindow.__init__`'s return — if you only need
to verify import paths after moving/renaming files, a plain
`importlib.import_module` sweep over every `interface/**/*.py` is a much
faster, sufficient check that needs no GUI at all.
