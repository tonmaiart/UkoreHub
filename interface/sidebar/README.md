# interface/sidebar/

The left-hand navigation column of `MainWindow` — replaced the old
horizontal top `MenuBar` row (renamed from `interface/menu_bar/`). A plain
widget column (repo identity, the section tab list, sync progress), not
Qt's `QMenuBar`/dropdown-menu widget.

- `sidebar.py` — `Sidebar`: top to bottom, `ActiveRepoWidget` (thumbnail +
  name label, display-only — see below), `SectionTabList` (stretched to
  fill the remaining height), then a footer strip (`sidebarFooter`) holding
  sync status, one widget per `interface/sidebar_footer_action_registry.py`
  entry (built via `spec.widget_factory()`, stored in
  `self.footer_action_widgets` keyed by `spec.key`; nothing here is
  hardcoded, Sidebar just renders whatever's registered — currently no
  plugin contributes a footer action (cloud sync moved to a zero-config
  shared R2 key, see the `ukorehub-cloud-sync` skill, so there's no more
  per-artist login/settings window to open from here); each footer-action
  widget would render as its own full-width row, above the account row),
  then an account row —
  `account_label` (display-only GitHub username, pushed in by
  `MainWindow._start_app` from `local_config_store.github_username`; no
  login/logout control of its own — actual GitHub login now happens
  entirely in the launcher exe before this app ever opens, see
  `updater.py (UkoreHubLauncher repo)`, and logout lives in
  Settings > Common, see `interface/settings/README.md`) plus the
  icon-only `setting_button`. Fixed width (`SIDEBAR_WIDTH`). `setting_button`
  is the only hardcoded app-level control left here — not a row in
  `SectionTabList`, since it's app-level, not repo-scoped.
- `active_repo_widget.py` — `ActiveRepoWidget`: the thumbnail banner
  (`_ThumbnailBanner`, fill-cropped, never rounded) plus a plain
  `name_label` beneath it naming the active Project/Repo. Re-added
  2026-07-15 as **display-only** — unlike the original version (removed
  earlier the same day), there's no click-to-open-picker button anymore:
  the active repo is switched exclusively by clicking a node in Project
  Editor's always-visible graph panel (`plugins/core/project_editor/`),
  not from here. `MainWindow` pushes
  into it directly (`set_active_labels`/`set_thumbnail`) from
  `_restore_active_repo`/`_set_active_repo`/`_on_repo_thumbnail_changed`.
- `section_tab_list.py` — `SectionTabList`: a vertical `QListWidget`, one
  row per registered `SectionRegistry` section — Explorer/Submit/About/
  Project Editor today (Project Editor used to be excluded here, docked
  permanently beside `view_stack` instead via `SectionSpec.persistent=True`,
  now removed — folded into an ordinary row/page like everything else).
  Emits `navigation_changed(key)` for every row.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, or touches `main_window.py`'s wiring (which constructs
`Sidebar` and connects its signals).
