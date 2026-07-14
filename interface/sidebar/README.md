# interface/sidebar/

The left-hand navigation column of `MainWindow` — replaced the old
horizontal top `MenuBar` row (renamed from `interface/menu_bar/`). A plain
widget column (repo identity, the section tab list, sync progress, GitHub
account), not Qt's `QMenuBar`/dropdown-menu widget.

- `sidebar.py` — `Sidebar`: top to bottom, `ActiveRepoWidget` (thumbnail +
  "Project / Repo" picker button), `SectionTabList` (stretched to fill the
  remaining height), then a footer strip (`sidebarFooter`) holding sync
  status, the Update button, and an account row —
  `interface/login/github_auth_widget.py`'s `GitHubAuthWidget` (constructed
  with `show_toggle_button=False`, avatar+username only — logging out lives
  in Settings > Common now) plus the icon-only `setting_button` right after
  it. Fixed width (`SIDEBAR_WIDTH`). Setting is deliberately its own button
  here, not a row in `SectionTabList` — it's an app-level control, not a
  repo-scoped one — so `MainWindow` deselects `tab_list`'s current row by
  hand when Setting is clicked (`_on_settings_requested`) rather than the
  list having any notion of a "Setting" entry itself.
- `active_repo_widget.py` — `ActiveRepoWidget`: owns the thumbnail banner
  (`_ThumbnailBanner`, fill-cropped, never rounded, no text overlay — the
  repo name is only ever shown once, on `select_button` below it) and the
  full-width "Project / Repo" button that opens the repo picker
  (`interface/login/repo_picker.py`).
- `section_tab_list.py` — `SectionTabList`: a vertical `QListWidget`, one
  row per registered `SectionRegistry` section (built-in and
  plugin-provided alike, in registry order) — Explorer/Submit/About today —
  then one row per dynamic Browser Link on the active repo (`add_dynamic_tab`,
  rebuilt by `main_window.py` on every repo switch, always inserted right
  after the fixed sections). Emits `navigation_changed(key)` for every row.
- `circular_pixmap.py` — `circular_pixmap` (crop-to-circle), used by
  `interface/login/github_auth_widget.py`'s GitHub avatar.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, or touches `main_window.py`'s wiring (which constructs
`Sidebar` and connects its signals) or a `login/`/`shared/` file these
import.
