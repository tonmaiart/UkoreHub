# plugins/studio/unity_hub/

Adds one sidebar tab with a single "Open Unity Hub" button — nothing else.
A single-file plugin (like `plugins/studio/software_linker/`), not
multi-file (see `plugins/README.md`'s "Multi-file plugins" section for why
that's a different setup).

- `manifest.json` — plugin id `unity_hub`, entry point `plugin.py`.
- `plugin.py`:
  - `register(api)` first makes sure a "Unity Hub" `Program` exists in the
    shared Program Database (`api.programs`, adding one if missing) purely
    so it shows up in Settings > Software Linker for the user to link a
    local `Unity Hub.exe` path to — no manual Program Database setup step
    needed first.
  - Registers one `SectionSpec` (`UnityHubPage`, order 40 — after Explorer=10/
    Submit=20/About=30). The page's only control is "Open Unity Hub".
  - On click, resolves the linked path the same way
    `plugins/studio/maya_launcher` finds `maya.exe`: reads
    `api.plugin_config_store("software_linker", shared=False).get(program.id)`
    (per-machine, set by the user under Settings > Software Linker). If
    nothing is linked yet, shows a message pointing at that tab instead of
    silently doing nothing.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive or touches `interface/settings_tab_registry.py`'s wiring.
