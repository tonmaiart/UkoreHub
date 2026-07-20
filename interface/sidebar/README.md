# interface/sidebar/

The left-hand navigation column of `MainWindow` — replaced the old
horizontal top `MenuBar` row (renamed from `interface/menu_bar/`). A plain
widget column (repo identity, the section tab list, sync progress, GitHub
account), not Qt's `QMenuBar`/dropdown-menu widget.

- `sidebar.py` — `Sidebar`: top to bottom, `ActiveRepoWidget` (thumbnail +
  name label, display-only — see below), `SectionTabList` (stretched to
  fill the remaining height), then a footer strip (`sidebarFooter`) holding
  sync status, one widget per `interface/sidebar_footer_action_registry.py`
  entry (built via `spec.widget_factory()`, stored in
  `self.footer_action_widgets` keyed by `spec.key` — e.g.
  `plugins/studio/self_updater/`'s Update button; nothing here is
  hardcoded, Sidebar just renders whatever's registered), and an account
  row — `interface/login/github_auth_widget.py`'s `GitHubAuthWidget` (display-only,
  avatar+username, no login/logout control of its own — logging out lives
  in Settings > Common now) plus the icon-only `setting_button` right after
  it. Fixed width (`SIDEBAR_WIDTH`). Setting is deliberately its own button
  here, not a row in `SectionTabList` — it's an app-level control, not a
  repo-scoped one — so `MainWindow` deselects `tab_list`'s current row by
  hand when Setting is clicked (`_on_settings_requested`) rather than the
  list having any notion of a "Setting" entry itself.
- `active_repo_widget.py` — `ActiveRepoWidget`: the thumbnail banner
  (`_ThumbnailBanner`, fill-cropped, never rounded) plus a plain
  `name_label` beneath it naming the active Project/Repo. Re-added
  2026-07-15 as **display-only** — unlike the original version (removed
  earlier the same day), there's no click-to-open-picker button anymore:
  the active repo is switched exclusively by clicking a node in Project
  Editor's always-visible graph panel (`plugins/studio/project_editor/`),
  not from here. `MainWindow` pushes
  into it directly (`set_active_labels`/`set_thumbnail`) from
  `_restore_active_repo`/`_set_active_repo`/`_on_repo_thumbnail_changed`.
- `section_tab_list.py` — `SectionTabList`: a vertical `QListWidget`, one
  row per registered `SectionRegistry` section **excluding** any
  `SectionSpec.persistent=True` section (Project Editor — see
  `interface/section_registry.py` and `interface/main_window.py`'s
  `_build_main_ui`, which docks a persistent section beside `view_stack`
  in a `QSplitter` instead of giving it a row here) — Explorer/Submit/About
  today — then one row per dynamic Browser Link on the active repo
  (`add_dynamic_tab`, rebuilt by `main_window.py` on every repo switch,
  always inserted right after the fixed sections). Emits
  `navigation_changed(key)` for every row.
- `circular_pixmap.py` — `circular_pixmap` (crop-to-circle), used by
  `interface/login/github_auth_widget.py`'s GitHub avatar.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, or touches `main_window.py`'s wiring (which constructs
`Sidebar` and connects its signals) or a `login/`/`shared/` file these
import.
