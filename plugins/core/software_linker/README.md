# plugins/core/software_linker/

Lets the user link each Program Database entry (each Project's own
`Project.programs`, `core/models.py` — not shared across Projects, see
`core/store.py`'s `MetadataStore.list_programs`/`get_program`) to a local
executable path on this machine — per-machine data, since "what's
installed here" is never team-shared. Reads `local_config_store.active_project_id`
directly (no Project selector of its own anymore — removed as of the
single-project-per-session change, since that id is now fixed for the
whole run by `launcher.py`'s mandatory Project Selector gate). A single-file plugin (unlike
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
    back to a generic icon), name/path/status each on their own line, and
    its own "Browse Program..." split button (dropdown holds "Browse
    Path...", folded into the same button rather than a separate one) +
    "Clear" button — no page-level selection state, each card acts on its
    own program directly.
  - `SoftwareLinkerPage` — the Settings tab itself: the active project's
    name (read-only) plus a scrollable list of `_ProgramLinkCard`s, one per
    Program Database entry in that project. Auto-detects an unlinked
    program's executable via a PATH lookup on first load per project
    (best-effort, never overwrites an existing link).
  - `register(api)` — registers `SoftwareLinkerPage` as a Settings tab via
    `api.register_settings_tab(...)`. The page's `config_store` is
    `api.plugin_config_store(PLUGIN_ID, shared=False)` — per-machine, keyed
    by Program id. **Other plugins read this same mapping** by
    calling `api.plugin_config_store("software_linker", shared=False)`
    themselves (e.g. `plugins/repo_internal/maya_launcher/plugin.py` reading a
    linked `maya.exe` path) — no coupling API needed, just agreeing on the
    `"software_linker"` id string. See `plugins/README.md`'s "Sharing data
    with another plugin" section.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive or touches `interface/settings_tab_registry.py`'s wiring.
