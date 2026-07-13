---
name: ukorehub-interface
description: Reference for UkoreHub's interface/ layer (C:\Tonmai\UkoreHub) — the PySide6 GUI: MainWindow's Menu Bar / Repo-Setting tab switcher, the five extension registries (SectionRegistry, SettingsTabRegistry, ProjectInfoTabRegistry, RepoAddonPanelRegistry, FileOpenerRegistry), PluginAPI composition, and the builtin_*.py dogfooding pattern. Use this whenever adding a page, a settings tab, a sidebar section, a Project Info tab, a Repo Add-on panel, or any UI-facing plugin/add-on registration — or whenever the task touches interface/main_window.py, interface/pages/, interface/plugin_api.py, or any interface/*_registry.py, even if the user doesn't say "interface" explicitly (e.g. "add a settings page", "show this in the sidebar").
---

# UkoreHub interface/ — architecture reference

`interface/` is the PySide6 GUI layer sitting on top of the Qt-free `core/`
(see the `ukorehub-core` skill for that side). Read `interface/README.md`
first for the current file listing — this skill is the architecture and the
*why*, kept deliberately shorter than a file index.

## Scoped editing

A task about `interface/` stays inside `interface/` — don't open `core/` or
`add-on/` files unless the change genuinely needs a new `core/` primitive
to build on. Within `interface/`, `pages/` and `settings_pages/` are each a
flat directory of independent, mostly-unrelated files (one file per
sidebar section / settings tab) — reading one page has no information
value for editing a different one, so open only the page/tab the task
names, plus `main_window.py` or the relevant `*_registry.py` only if the
task is about wiring, not page content. Same for `*_dialog.py` and
`*_worker.py`: pick the one the task names, don't survey the others.

## MainWindow structure — no more modal Settings dialog

`interface/main_window.py`'s `MainWindow` no longer opens a modal
`QDialog` for settings (that was ripped out in favor of an embedded tab
switcher), and there is no separate bottom switcher bar anymore either —
everything lives in one row. Current structure, top to bottom:

- **Menu Bar** (`interface/menu_bar.py`, top of window — this is what used
  to be the bottom status bar before it was moved and renamed; don't
  confuse it with Qt's `QMenuBar`, it's UkoreHub's own term for this
  strip). It embeds **`TopTabBar`** (`interface/top_tab_bar.py`, right after
  the app label): one button per `SectionRegistry` section
  (Repo/Explorer/Submit/About, in registry order), in its own exclusive
  button group. A separate **Setting** button lives at the *far end* of the
  same row, after GitHub login/logout — deliberately its own control, not
  part of `TopTabBar`'s group, since it's an app-level setting, not
  repo-scoped. `MainWindow` keeps the two in sync by hand
  (`TopTabBar.uncheck_all()` / `menu_bar.setting_button.setChecked(...)`)
  since they're independent `QButtonGroup`s. There is no per-section button
  list in the sidebar anymore (`sidebar.py` is now just thumbnail + repo
  picker + recent files).
- **A view stack** (`MainWindow.view_stack`) with three kinds of page:
  the shared **repo view** (sidebar + `content_stack`, for sections with
  `SectionSpec.standalone=False` — built-in Repo/About), one **standalone
  full-width page per section** with `standalone=True` (built-in
  Explorer/Submit — no sidebar), and the **settings view**
  (`SettingsTabRegistry`-driven, shown when the separate Setting button is
  clicked). `TopTabBar.tab_changed` picks between the repo view and a
  standalone page; `MenuBar.settings_requested` picks the settings view.
- Every settings page **self-persists on every change** — there is no
  Save/Cancel step anywhere. `SettingsTabSpec` has no `on_save`/`on_cancel`
  hooks; if you're writing a new settings page, write directly through
  whatever store you're editing the moment the user changes a value, the
  same way every existing settings page does.

## The five registries

All live under `interface/`, except `FileOpenerRegistry` which is Qt-free
and therefore lives in `core/extensibility/` (see `ukorehub-core` skill) —
don't go looking for it here, even though it's UI-adjacent in purpose.

| Registry | Spec dataclass | Keyed? | Purpose |
|---|---|---|---|
| `SectionRegistry` | `SectionSpec` | yes, rejects dup keys | Top-level tab-bar sections, rendered by `TopTabBar` (Repo, Explorer, Submit, About, ...) |
| `SettingsTabRegistry` | `SettingsTabSpec` | yes | Tabs shown in the "Setting" view |
| `ProjectInfoTabRegistry` | `ProjectInfoTabSpec` | yes | Sub-tabs inside the Project Info page (it's a tab-of-tabs) |
| `RepoAddonPanelRegistry` | (factory keyed by addon_id) | yes | Per-add-on status panel shown in the "Repo Add-on" tab of Project Info |
| `FileOpenerRegistry` | `FileOpenerSpec` | **no**, plain list, first-match-wins | Add-on can claim responsibility for opening a file extension (lives in `core/`) |

Every registered page/tab factory follows the same **`page_factory: Callable[[], QWidget]`** convention — no arguments, construct-on-demand. This is also why pytest can smoke-test registries without ever instantiating a real `QWidget`: tests register `page_factory=lambda: None` and only assert on registry bookkeeping (duplicate-key rejection, ordering), never call the factory.

Built-ins register into the exact same registries a plugin/add-on would —
`interface/builtin_sections.py`, `interface/builtin_settings_tabs.py`,
`interface/builtin_project_info_tabs.py` call the same
`register_*`/`api.register_*` surface as `add-on/MayaLauncher/plugin.py`
does. This "dogfooding" is deliberate: if a built-in page needs something
the registry API can't express, that's a signal the registry API itself is
incomplete — don't special-case built-ins with a side channel.

## `interface/plugin_api.py` — `PluginAPI`

The single object passed to every plugin's/add-on's `register(api)`. It's a
pure composition/facade over already-constructed services — it does not
construct anything itself, everything is handed in via `launcher.py`.
Current constructor:

```python
def __init__(self, *, store, program_store, local_config_store, git_service, hooks,
             section_registry, settings_tab_registry, project_info_tab_registry,
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
  share the same file — see `ukorehub-maya-launcher-addon` skill for the
  live example (MayaLauncher reads SoftwareLinker's config this way).
- `api.app_root` → `Path` to the UkoreHub install root itself (i.e.
  `launcher.py`'s own `REPO_ROOT`), for add-ons that need to reference other
  paths inside the UkoreHub installation (like
  `plugins/MayaToolkit/`) without guessing their nesting depth from
  `__file__`.
- `api.register_repo_addon_panel(addon_id, panel_factory)`,
  `api.register_file_opener(addon_id, extensions, opener)`,
  `api.register_section(...)`, `api.register_settings_tab(...)`,
  `api.register_project_info_tab(...)` — one register method per registry
  above.

## Page protocol: `set_repo()`

Most pages that need to react to the active repo changing (Repo Browser,
Repo About, Git Status, Project Info, and its Repo Add-on sub-tab) implement
a `set_repo(repo: Repo | None) -> None` method, called by `MainWindow`/the
owning page whenever the sidebar selection changes. If you're adding a new
page that cares which repo is active, implement this method rather than
inventing a new callback — it's how every existing page stays in sync.

## File-open flow — where an add-on actually intercepts a double-click

This is the one flow worth tracing end-to-end since it crosses several
files and the naming ("open") appears at every layer:

1. `interface/repo_browser/browser_widget.py`'s `RepoBrowserWidget` takes an
   `open_file: Callable[[Path], None] | None = None` constructor param
   (default `None` falls back to `core.os_utils.open_with_default_app`,
   i.e. the OS file association / `os.startfile`). Double-clicking a row
   calls `self._open_file(path)`, then unconditionally emits
   `file_opened.emit(path)` regardless of which opener handled it.
2. `interface/pages/repo_browser_page.py`'s `RepoBrowserPage` constructs
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
4. `interface/main_window.py`'s `_on_recent_file_activated` (Recent Files
   sidebar list) mirrors the exact same check-registry-then-fallback logic
   independently, for consistency — clicking a recent file goes through the
   same add-on opener as double-clicking it in Repo Browser.

If you add a new file-open entry point (e.g. a "reveal in explorer" style
action, or another sidebar list), replicate this same
check-registry-then-fallback shape rather than calling
`open_with_default_app` directly, so add-on-provided openers stay
consistent everywhere a file can be opened from.

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
pytest test: construct `QApplication`, all registries, and `MainWindow`
without calling `app.exec()`, `patch.object` any dialog-showing methods
(`_show_launch_dialog`, `_check_for_update`) to no-ops, and end with
`sys.stdout.flush(); os._exit(0)` — `os._exit` is required because Qt/
Windows can hang on normal process teardown after `QApplication` is
destroyed without an explicit `app.quit()`; without the `os._exit(0)` the
script can look hung even though it actually finished.
