# plugins/studio/UkoreBrowser/

Maya-side asset browser — a standalone tool launched from inside Maya (not a
UkoreHub UI panel). Extracted out of `add-on/MayaToolkit` on 2026-07-13;
folded into `plugins/studio/maya_launcher/UkoreBrowser/` as one of 7 nested
tools during the 2026-07-14 consolidation; split back out to this top-level
plugin on 2026-07-19 (see `plugins/studio/maya_launcher/README.md` for why).
Still depends on MayaToolkit's `tmlib`/`UkoreMaya` packages **and** on
`plugins/studio/PublishApi` staying on PYTHONPATH (see "External
dependencies" below), so both must stay enabled alongside this plugin for
it to keep working.

## Shape

- `manifest.json` / `plugin.py` — standard plugin registration (see
  `plugins/README.md`). `plugin.py` contributes PYTHONPATH entries to
  `plugins/studio/maya_launcher/`'s shared `maya_launcher_env_bridge`
  `PluginConfigStore` (same convention as
  `plugins/studio/MayaToolkit/plugin.py`) — no file opener, since this
  tool is launched explicitly from a Maya menu, not triggered by opening a
  file. No direct import relationship with `maya_launcher` — just the
  shared `PluginConfigStore` id convention. **Also** registers a
  `CATEGORY_REPO` Settings tab (`settings_page.py`, see below) — a
  UkoreHub-side page, not Maya-side, unlike everything else `plugin.py`
  does.
- `settings_page.py` — `UkoreBrowserSettingsPage`: the "Repo Studio
  Setting" tab (Repository Setting popup > Ukore Browser) — unlike
  `ModelPublisher`/`RigPublisher`/`AnimationPublisher`'s single-select
  "which pipeline connection does this tool publish into" pickers, this
  is a **multi-select** checkbox list (one row per active-repo pipeline
  connection) letting a studio admin hide specific connections from
  the root-tab row without removing the pipeline connection itself —
  UkoreBrowser genuinely wants to show several root tabs at once, unlike
  the Publishers which each need exactly one destination. Stores the
  *hidden* set (opt-out), not the shown set, in this plugin's own
  `PluginConfigStore` — **`data/plugins/studio/ukore_browser.json`, key
  `"repo_hidden_root_tabs"`. Not to be confused with**
  `<browsed repo root>/.ukorehub/ukore_browser.json` (`browser_config.py`'s
  recent-files cache, below) — same base filename, completely different
  location and purpose: this one lives inside UkoreHub's own install,
  that one lives inside whichever production repo is being browsed.
  Read back on the Maya side by `core/repo_context.py`'s
  `get_pipeline_root_tabs()`.
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
      active repo, delegating to `plugins/studio/PublishApi`'s
      `repo_paths` module (`get_active_repo()`, `get_pipeline_refs()`,
      `resolve_ref()`) rather than constructing its own
      `core.store`/`core.paths` calls — same source of truth
      `ModelPublisher`/`RigPublisher`/`AnimationPublisher` build their
      publish-root resolution on. Falls back to Maya's current workspace
      dir if there's no active repo.
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

## External dependencies (MayaToolkit + PublishApi)

This plugin does **not** vendor `tmlib` or `UkoreMaya` — both packages
still live at `plugins/studio/MayaToolkit/maya-scripts/{tmlib,UkoreMaya}/` and are
imported by name (`tmlib.ui.interface_template`, `tmlib.module.PySide`,
`UkoreMaya.core.template_ui`, `UkoreMaya.core.menu_utils`,
`UkoreMaya.core.function`). It also doesn't vendor its own repo/pipeline
path-resolution logic anymore as of 2026-07-19 — `core/repo_context.py`
imports `PublishApi.repo_paths` instead (see below). Both of these only
resolve because `plugins/studio/MayaToolkit/plugin.py` and
`plugins/studio/PublishApi/plugin.py` each contribute their own
`maya-scripts/` folder to the same `maya_launcher_env_bridge` PYTHONPATH
bridge this plugin uses — **if either is ever disabled for a repo (via
`plugins/studio/maya_launcher/`'s `RepoToolsStore` toggle), UkoreBrowser
breaks.** Don't "fix" this by vendoring `tmlib`/`UkoreMaya`/`PublishApi`'s
logic in here without a deliberate decision to do so; see
`plugins/studio/maya_launcher/README.md` for the general shape of the
bridge convention every Maya tool plugin here relies on.

## Root-path detection

`core/repo_context.get_root_path()` is the entry point for `self.root_path`
(what the Miller-column project/class/scene/shot/element lists and the
file-system model are rooted at): (1) the active UkoreHub repo (via
`PublishApi.repo_paths.get_active_repo()` — see "External dependencies"
above) if set; (2) `cmds.workspace(q=True, rd=True)`. There is no more
hardcoded drive path — don't reintroduce one. **Deliberately not** the
current scene file's folder — that used to be priority 1, but rooting the
Miller columns at the scene's own (usually leaf, subfolder-less) folder
left all 5 of them permanently empty.

Where the browser lands on open (`self.current_browse_path`) is separate:
`get_initial_browse_path(root_path)` returns the current scene file's
folder if one is open and it's actually inside `root_path`, else
`root_path` itself — so you still start out where you're working, without
that affecting what the columns are rooted at.

## Pipeline root tabs

`core/repo_context.get_pipeline_root_tabs()` calls
`PublishApi.repo_paths.get_pipeline_refs()`/`resolve_ref()`/
`get_custom_path()` (same source of truth `ModelPublisher`/`RigPublisher`/
`AnimationPublisher` resolve their publish root through — see
`plugins/studio/PublishApi/README.md`) and returns the active repo plus
every repo it has connected to via "Connect Pipeline Input Path..." in
Project Editor, each resolved down to its specific declared `CustomPath`
rather than just the target repo's root (e.g. `RigPublish`'s "Character"
`CustomPath`, not all of `RigPublish`), as `{"label", "path"}` dicts —
minus whichever refs a studio admin has hidden via this plugin's own Repo
Studio Setting tab (`settings_page.py`, `_get_hidden_root_tab_keys`, see
above).
`ui/main_window.py`'s `_build_root_tabs()` turns this into a row of
checkable buttons inserted at row 0 of the central grid layout (unused by
`ui.ui`, whose own rows start at 1) — clicking one calls `_switch_root(path)`,
which re-points `root_path`, the recent-files `BrowserConfig`, the
`QFileSystemModel`, and the Miller columns at that repo, same shape
`__init__` uses to set things up the first time. No-ops entirely (no tab
row added) if there's no active repo.

## Working on this plugin

Read/edit only files under this folder for a UkoreBrowser-only task — see
`plugins/README.md`'s plugin-scoping note (and the `ukorehub-plugin` skill)
for why sibling plugins shouldn't be opened unless the task explicitly
touches them.
