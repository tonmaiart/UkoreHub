# plugins/studio/software_linker/

Lets the user link each Program Database entry (`core/program_store.py`) to
a local executable path on this machine — per-machine data, since "what's
installed here" is never team-shared. A single-file plugin (unlike
`plugins/studio/explorer/`/`submit/`, which are multi-file — see
`plugins/README.md`'s "Multi-file plugins" section for why that's a
different setup).

- `manifest.json` — plugin id `software_linker`, entry point `plugin.py`.
- `plugin.py` — everything in one file:
  - `list_installed_programs()` / `_resolve_exe_path()` — best-effort scan
    of Windows' Uninstall registry keys (the same list "Programs and
    Features"/Settings > Apps reads from).
  - `ProgramPickerDialog` — icon+search picker over installed programs.
  - `SoftwareLinkerPage` — the Settings tab itself: list of Program
    Database entries + their linked path, "Browse Program...", "Browse
    Path...", "Clear Link". Auto-detects an unlinked program's executable
    via a PATH lookup on first load (best-effort, never overwrites an
    existing link).
  - `register(api)` — registers `SoftwareLinkerPage` as a Settings tab via
    `api.register_settings_tab(...)`. The page's `config_store` is
    `api.plugin_config_store(PLUGIN_ID, shared=False)` — per-machine, keyed
    by Program id. **Other plugins/add-ons read this same mapping** by
    calling `api.plugin_config_store("software_linker", shared=False)`
    themselves (e.g. `add-on/MayaLauncher/plugin.py` reading a linked
    `maya.exe` path) — no coupling API needed, just agreeing on the
    `"software_linker"` id string. See `plugins/README.md`'s "Sharing data
    with another plugin" section.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive or touches `interface/settings_tab_registry.py`'s wiring.
