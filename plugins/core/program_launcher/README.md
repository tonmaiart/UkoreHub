# plugins/core/program_launcher/

Adds one sidebar tab (icon `data/icons/icons8-booster-64.png`) listing
every Program the active repo requires (`Repo.required_program_ids`) — a
generic launcher, not tied to any one piece of software (this plugin used
to be `unity_hub`, a single "Open Unity Hub" button; renamed and
generalized 2026-08-03). A single-file plugin (like
`plugins/core/software_linker/`), not multi-file (see
`plugins/README.md`'s "Multi-file plugins" section for why that's a
different setup).

- `manifest.json` — plugin id `program_launcher`, entry point `plugin.py`.
- `plugin.py`:
  - Registers one `SectionSpec` (`ProgramLauncherPage`, order 40 — after
    Explorer=10/Submit=20/About=30), wired (`wire=_wire`) to
    `SectionHost.open_settings_tab` via `bind_open_settings_tab` so its own
    "Software Linker Setting" shortcut button (always visible in the
    header, regardless of which cards are linked) can jump straight to
    Settings > Software Linker.
  - `set_repo(project, repo, workspace_root)` (the standard per-page
    protocol every `SectionSpec` page implements) rebuilds the card grid
    whenever the active repo changes.
  - One square `_ProgramCard` per Program in `repo.required_program_ids`
    (resolved via `api.programs.get_program`, skipping any id that no
    longer exists in the catalog), laid out in a wrapping grid
    (`QListWidget` in `IconMode`, one card per `QListWidgetItem` via
    `setItemWidget` — native Qt grid reflow on resize, no hand-rolled flow
    layout). Each card shows the Program's own icon (`ProgramStore.
    resolve_icon_path`, same icon Settings > Program Database manages —
    falls back to a generic icon if none is set) with name + version
    below it.
  - Resolves the pinned version (`repo.program_version_pins`, same lookup
    `plugins/repo_internal/maya_launcher/link_resolution.py`'s `pinned_version()`
    does) and the linked executable path the same way
    `plugins/repo_internal/maya_launcher` finds `maya.exe` — reads
    `api.plugin_config_store("software_linker", shared=False).get(key)`
    (per-machine, set by the user under Settings > Software Linker).
    `_linked_key`/`_pinned_version` here are convention-only duplicates of
    `plugins/core/software_linker/plugin.py`'s and
    `plugins/repo_internal/maya_launcher/link_resolution.py`'s own copies — keep
    all three in sync if that key shape ever changes.
  - No separate per-card buttons — the card itself is the control.
    Double-clicking an unlinked card (shown with a "Not linked" caption)
    opens the Setting popup straight on the Software Linker tab, same as
    the header shortcut button. Double-clicking a linked card checks
    `api.program_launch_registry.find_launcher(program)`
    (`interface/program_launch_registry.py`) first — a plugin (currently
    only `plugins/repo_internal/maya_launcher`, for anything named "maya") can
    contribute its own launch behavior instead of a bare
    `subprocess.Popen` of the raw linked exe, e.g. Maya's
    setProject/env-merge/force-load-plugins wiring. No match found falls
    back to `subprocess.Popen([exe_path])` directly.
  - No active repo, or a repo with no required Programs, shows a status
    label instead of an empty grid.

Cross-plugin/interface wiring this needed, beyond this folder:
- `interface/section_registry.py`'s `SectionHost` gained an
  `open_settings_tab(key)` field.
- `interface/settings/settings_view.py`'s `SettingsView`/`SettingsDialog`
  gained a `select_tab(key)` method.
- `interface/main_window.py`'s `_on_settings_requested` gained an optional
  `select_key` param, and `_build_main_ui`'s `SectionHost(...)` construction
  wires `open_settings_tab` to it.
- `interface/program_launch_registry.py` is a brand-new registry
  (`ProgramLaunchRegistry`/`ProgramLaunchSpec`), plumbed through
  `interface/plugin_api.py` (`api.register_program_launcher`,
  `api.program_launch_registry`) and constructed in `launcher.py` — see
  `plugins/repo_internal/maya_launcher/README.md`'s "Standalone launch for
  plugins/core/program_launcher/" section for the contributing side.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive or touches the `open_settings_tab`/`program_launch_registry`
wiring above.
