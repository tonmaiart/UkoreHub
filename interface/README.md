# interface/

PySide6 GUI layer for UkoreHub. Builds on `core/` for all data and git
operations — widgets here handle layout, user interaction, and background
`QThread` workers so the UI doesn't block on git/network calls.

**Working here:** stay inside `interface/` unless the change needs a new
`core/` primitive to build on — don't open `core/` or `add-on/` files
otherwise. `pages/` and `settings_pages/` are each a flat directory of
independent, mostly-unrelated files (one per sidebar section / settings
tab) — open only the one the task names, not the whole folder.

- `main_window.py` — top-level `QMainWindow`: sidebar + stacked content pages,
  menu bar (sync progress, GitHub login, top tab bar), active-repo restore and
  auto-sync on launch.
- `menu_bar.py` / `top_tab_bar.py` — the single top row: app label, the
  `TopTabBar` (one button per `SectionRegistry` section — Repo/Explorer/
  Submit/About — its own exclusive group), sync progress, GitHub
  login/logout, then a separate "Setting" button at the far end (not part
  of `TopTabBar`'s group — it's an app-level control, not repo-scoped).
- `sidebar.py` / `sidebar_thumbnail.py` — left navigation: project/repo picker,
  repo thumbnail, recent files (no longer owns section switching — that
  moved to `top_tab_bar.py`).
- `section_registry.py` / `settings_tab_registry.py` / `project_info_tab_registry.py`
  — open, ordered registries sections, settings tabs, and Project Info
  sub-tabs register into (built-in and plugin-provided alike), replacing the
  old closed `SectionKey` enum. `repo_addon_panel_registry.py` is a fourth,
  simpler one — a plain `addon_id -> panel_factory` lookup (not ordered) for
  the "Repo Add-on" tab.
- `builtin_sections.py` / `builtin_settings_tabs.py` / `builtin_project_info_tabs.py`
  — construct the built-in pages/tabs and register them into the registries
  above, exactly as a plugin would register its own.
- `plugin_api.py` — `PluginAPI`, the object passed to every plugin's *and
  add-on's* `register(api)` entry point (mechanically identical — same object,
  same capabilities, just discovered from `plugins/` vs. the separate
  `add-on/` catalog); composes `core/` services with the
  section/settings-tab/project-info-tab/repo-addon-panel registries (see
  `core/extensibility/loader.py`).
- `circular_pixmap.py` — shared helper clipping a `QPixmap` to a circle, used
  by the GitHub status-bar avatar and the sidebar repo-thumbnail badge.
- `pages/` — one page per sidebar section: `project_info_page.py` (a
  `QTabWidget` shell — the built-in "Main" tab lives in
  `project_info_main_tab.py`, the built-in "Repo Add-on" tab lives in
  `repo_addon_tab.py` and renders each enabled add-on's per-repo preference
  panel, plugins/add-ons can add more via `PluginAPI.register_project_info_tab`),
  `repo_browser_page.py`, `repo_git_status_page.py`, `repo_about_page.py`
  (Requirements/Enabled-Add-ons shown as `RequirementCard`/`AddonCard`
  widgets, not plain list rows).
- `repo_browser/` — the file browser widget used by the Repo Browser page
  (column/table file view + per-path commit history panel).
- `settings_pages/` — tabs inside the Settings dialog: common settings,
  program database, project data editor, project sync status, and a
  read-only `plugins_page.py` listing what got discovered under `plugins/`.
  (Color theme selection was removed from the UI — `core/theme.py` and the
  saved `theme` field in `local_config.json` still exist, just unpickable.)
- `*_dialog.py` — modal dialogs: launch/quick-start, commit message, merge
  conflict resolution, GitHub login, repo picker, program editor, settings
  shell.
- `*_worker.py` — `QThread` subclasses that run git/network calls off the UI
  thread (clone/pull/push, status, commit log, per-path commit history,
  GitHub auth, avatar download).
- `github_auth_widget.py` — status bar login/logout button + username display.
- `theme_apply.py` — applies a `core.theme` stylesheet to the `QApplication`.
- `log_panel.py` — scrolling read-only log output used during sync/push/pull.
