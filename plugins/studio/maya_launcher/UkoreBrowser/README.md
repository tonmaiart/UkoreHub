# add-on/UkoreBrowser/

Maya-side asset browser — a standalone tool launched from inside Maya (not a
UkoreHub UI panel). Extracted out of `add-on/MayaToolkit` on 2026-07-13;
still depends on MayaToolkit's `tmlib`/`UkoreMaya` packages staying on
PYTHONPATH (see "External dependencies" below), so MayaToolkit must stay
enabled alongside this add-on for it to keep working.

## Shape

- `manifest.json` / `plugin.py` — standard add-on registration (see
  `add-on/README.md`). `plugin.py` only contributes PYTHONPATH entries to
  the shared `maya_launcher_env_bridge` (same convention as
  `add-on/MayaToolkit/plugin.py`) — no file opener or repo-addon panel,
  since this tool is launched explicitly from a Maya menu, not triggered by
  opening a file.
- `maya-scripts/UkoreBrowser/` — the Maya-side Python package, contributed
  to `PYTHONPATH` so `import UkoreBrowser` works inside Maya:
  - `interface.py` — **do not delete**: a one-line backward-compat shim
    (`from UkoreBrowser.ui.main_window import MainWindow`).
    `tmlib.core.File.launch("UkoreBrowser")` (called from
    `UkoreMaya/core/menu_utils.py:browser()` and the auto-launch hook in
    `UkoreMaya/core/function.py`) hardcodes the import path
    `UkoreBrowser.interface.MainWindow` — this file exists purely to keep
    that contract working without touching either caller.
  - `core/` — Qt-free logic:
    - `repo_context.py` — auto-detects the browse root from UkoreHub's own
      active repo (reads `core.store`/`core.paths` directly via a
      PYTHONPATH entry `plugin.py` also contributes), falling back to
      Maya's current workspace dir if there's no active repo.
    - `browser_config.py` — recent-files persistence, stored **relative to
      the repo root** under `<repo_root>/.ukorehub/ukore_browser.json` (one
      file per repo, not a single global file mixing every repo/project).
    - `version_filter.py` — pure "keep only the latest `_vNNN`" logic.
    - `file_ops.py` — plain filesystem ops (create/rename/delete/open in
      explorer).
    - `maya_ops.py` — the only file that touches `maya.cmds` /
      `UkoreMaya.core` (reference import, scene open/save, workspace set).
  - `ui/` — PySide widgets: `main_window.py` (`MainWindow`, wiring only —
    delegates all real work to `core/`), `file_model.py` (the extension /
    latest-version filter proxy model), `popup.py`, `menus.py`.
  - `ui.ui` — Qt Designer layout. Loaded by
    `tmlib.ui.interface_template.ToolkitWindow` via
    `importlib.import_module("UkoreBrowser")` + `__path__[0]/ui.ui` — this
    is why `MainWindow.__init__` hardcodes `super().__init__("UkoreBrowser")`
    instead of deriving the toolkit name from `__file__` (it now lives one
    level deeper, under `ui/`, than the original single-file version did).
  - `template/` — `template.ma`/`template.blend`, copied when creating a new
    scene file from the browser's "+" menu.

## External dependencies (still in MayaToolkit)

This add-on does **not** vendor `tmlib` or `UkoreMaya` — both packages
still live at `add-on/MayaToolkit/maya-scripts/{tmlib,UkoreMaya}/` and are
imported by name (`tmlib.ui.interface_template`, `tmlib.module.PySide`,
`UkoreMaya.core.template_ui`, `UkoreMaya.core.menu_utils`,
`UkoreMaya.core.function`). This only resolves because MayaToolkit's own
`plugin.py` contributes its `maya-scripts/` folder to the same
`maya_launcher_env_bridge` PYTHONPATH bridge this add-on uses — **if
MayaToolkit is ever disabled for a repo, UkoreBrowser breaks.** Don't "fix"
this by copying tmlib/UkoreMaya in here without a deliberate decision to do
so; see the `ukorehub-maya-launcher-addon` skill for the general shape of
the bridge convention both add-ons rely on.

## Root-path detection

`core/repo_context.get_root_path()` is the entry point for `self.root_path`
(what the Miller-column project/class/scene/shot/element lists and the
file-system model are rooted at): (1) the active UkoreHub repo (via
`core.store.LocalConfigStore` + `core.store.MetadataStore` +
`core.paths.resolve_repo_path`, all read directly since this tool's
PYTHONPATH contribution also includes UkoreHub's own app root) if set;
(2) `cmds.workspace(q=True, rd=True)`. There is no more hardcoded drive
path — don't reintroduce one. **Deliberately not** the current scene
file's folder — that used to be priority 1, but rooting the Miller columns
at the scene's own (usually leaf, subfolder-less) folder left all 5 of them
permanently empty.

Where the browser lands on open (`self.current_browse_path`) is separate:
`get_initial_browse_path(root_path)` returns the current scene file's
folder if one is open and it's actually inside `root_path`, else
`root_path` itself — so you still start out where you're working, without
that affecting what the columns are rooted at.

## Pipeline root tabs

`core/repo_context.get_pipeline_root_tabs()` reads
`data/plugins/studio/pipeline_architect.json` directly (same "construct
the store straight off disk" approach as `get_active_repo_path()` — Maya's
Python has no `PluginAPI` instance to call `plugin_config_store()` through)
and returns the active repo plus every repo declared as one of its
pipeline inputs/outputs there, as `{"label", "path"}` dicts.
`ui/main_window.py`'s `_build_root_tabs()` turns this into a row of
checkable buttons inserted at row 0 of the central grid layout (unused by
`ui.ui`, whose own rows start at 1) — clicking one calls `_switch_root(path)`,
which re-points `root_path`, the recent-files `BrowserConfig`, the
`QFileSystemModel`, and the Miller columns at that repo, same shape
`__init__` uses to set things up the first time. No-ops entirely (no tab
row added) if there's no active repo.

## Working on this add-on

Read/edit only files under this folder for a UkoreBrowser-only task — see
`add-on/README.md`'s add-on-scoping note (and the `ukorehub-addon` skill)
for why sibling add-ons shouldn't be opened unless the task explicitly
touches them.
