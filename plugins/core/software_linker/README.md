# plugins/core/software_linker/

Registers the sidebar's **"Program Launcher"** tab (icon
`assets/icons/icons8-booster-64.png`, order 40, after Explorer=10/Submit=20/
project_editor=15) — lets the user link each Program Database entry (each
Project's own `Project.programs`, `core/models.py` — not shared across
Projects, see `core/store.py`'s `MetadataStore.list_programs`/`get_program`)
to a local executable path on this machine, and double-click a linked card
to open it. Per-machine data, since "what's installed here" is never
team-shared. As of 2026-08-10 this replaced the old `plugins/core/
software_linker` **Settings tab** (`api.register_settings_tab`) — moved
wholesale to a top-level `SectionSpec` instead — and absorbed
`plugins/core/program_launcher/`'s launch behavior after that plugin was
retired the same day; `PLUGIN_ID` stays the literal string `"software_linker"`
regardless, since other plugins read the same `PluginConfigStore` id (see
below), independent of the tab's own label. A single-file plugin (unlike
`plugins/core/explorer/`/`submit/`, which are multi-file — see
`plugins/README.md`'s "Multi-file plugins" section for why that's a
different setup). See `core/extensibility/README.md` for the plugin
discovery mechanism.

- `manifest.json` — plugin id `software_linker`, entry point `plugin.py`.
- `plugin.py` — everything in one file:
  - `list_installed_programs()` / `_resolve_exe_path()` — best-effort scan
    of Windows' Uninstall registry keys (the same list "Programs and
    Features"/Settings > Apps reads from).
  - `ProgramPickerDialog` — icon+search picker over installed programs.
  - `_ProgramLinkCard` — one card per linkable (Program, version) slot:
    the Program's own icon (`MetadataStore.resolve_program_icon_path`, falling
    back to a generic icon), name/path/status each on their own line, its
    own "Browse Program..." split button (dropdown holds "Browse
    Path...", folded into the same button rather than a separate one) +
    "Clear" button — no page-level selection state, each card acts on its
    own program directly. **Double-clicking the card itself** (not the
    buttons — Qt delivers the event to whichever child widget is under the
    cursor first, so the buttons still just activate normally) opens the
    linked executable, or opens the same "Browse Program..." picker if
    nothing is linked yet — the same double-click-to-launch UX
    `plugins/core/program_launcher/`'s card grid used to have, now living
    here instead. A linked double-click first checks
    `api.program_launch_registry.find_launcher(program)`
    (`interface/program_launch_registry.py`) — a plugin (currently only
    `maya_launcher`, now its own `cache/plugins/` clone, for anything named
    "maya") can
    contribute its own launch behavior instead of a bare `subprocess.Popen`
    of the raw linked exe, e.g. Maya's setProject/env-merge/force-load-plugins
    wiring — using whichever repo is currently active (`SoftwareLinkerPage
    .set_repo`'s `repo` param); no match, or no active repo, falls back to
    `subprocess.Popen([exe_path])` directly.
  - `SoftwareLinkerPage` — the tab itself: the active project's name
    (read-only) plus a scrollable list of `_ProgramLinkCard`s, one per
    Program Database entry in that project (every Program in the Project's
    whole catalog, **not** filtered down to one repo's
    `required_program_ids` the way the retired `program_launcher` was —
    this page stays project-scoped). Implements the standard
    `SetRepoPage` protocol (`interface/page_protocols.py`) —
    `set_repo(project, repo, workspace_root)` is called whenever this
    becomes the visible section or the active repo changes
    (`interface/main_window.py`'s `_apply_to_current_page` /
    `_apply_set_repo`, optional-protocol per
    `developer/bug-history/2026-08-09-set-repo-not-optional-protocol-method.md`)
    — stores both `project` (which Program Database to list) and `repo`
    (passed through to a matched `ProgramLaunchSpec` on double-click).
    Auto-detects an unlinked program's executable via a PATH lookup on
    every rebuild (best-effort, never overwrites an existing link,
    `_auto_detect_missing`).
  - **"Auto-Resolve Path" button** (`_on_auto_resolve_path`) — a fuller,
    explicit, user-triggered scan for every still-unlinked Program in the
    active project, tried in order until one hits:
    1. System PATH (`shutil.which`, same check `_auto_detect_missing`
       already does automatically).
    2. The Windows Uninstall registry (`list_installed_programs`), matched
       by substring against the Program's own name.
    3. A small hardcoded table of default install locations for common
       DCCs (`_DEFAULT_INSTALL_GLOBS` — Maya, Unreal, Blender, Photoshop),
       glob-matched since the version number is baked into the install
       folder name.

    Deliberately kept separate from `_auto_detect_missing`'s silent,
    automatic PATH-only check — the registry/default-path sources are
    more likely to produce a wrong guess for a generically-named program,
    so they only run when the user explicitly clicks the button. Shows a
    summary message box ("Resolved N program(s)") and never overwrites an
    existing link, same rule as `_auto_detect_missing`.
  - `register(api)` — registers `SoftwareLinkerPage` as a top-level
    `SectionSpec` via `api.register_section(...)`. The page's
    `config_store` is `api.plugin_config_store(PLUGIN_ID, shared=False)` —
    per-machine, keyed by Program id. **Other plugins read this same
    mapping** by calling `api.plugin_config_store("software_linker",
    shared=False)` themselves (e.g. `maya_launcher`'s `plugin.py`
    reading a linked `maya.exe` path) — no coupling API needed, just
    agreeing on the `"software_linker"` id string. See
    `plugins/README.md`'s "Sharing data with another plugin" section.

## `interface/program_launch_registry.py` note

This plugin is the sole consumer of `ProgramLaunchRegistry`/
`find_launcher()` again (it was orphaned briefly between
`plugins/core/program_launcher/`'s retirement and this plugin picking up
double-click launch the same day) — `maya_launcher`'s (now its own
`cache/plugins/` clone) `plugin.py`'s `launch_maya_standalone` is still
the only contributed spec.
If this plugin's double-click launch is ever removed too, check whether
`interface/program_launch_registry.py`, its `plugin_api.py`/`launcher.py`
wiring, and `maya_launcher`'s `launch_maya_standalone` registration have
become dead code again before leaving them in place.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive or touches `interface/section_registry.py`'s wiring.
