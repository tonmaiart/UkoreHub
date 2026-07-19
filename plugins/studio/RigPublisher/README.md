# plugins/studio/RigPublisher/

Maya-side tool that publishes the active Rig scene (a raw Maya Ascii copy)
into a versioned folder. Split out of the original `UkorePublisher`
plugin's "Rig" branch on 2026-07-19, alongside
`ModelPublisher`/`AnimationPublisher` and the new `PublishApi` shared
library — see `plugins/studio/PublishApi/README.md` and
`plugins/studio/maya_launcher/README.md` for the bridge convention this
follows. Has its own dedicated UI now (no "Type" list — this plugin only
ever publishes Rig) instead of sharing one UI across every publish type
the way `UkorePublisher` used to.

## Files

- `manifest.json` — plugin id `rig_publisher`, entry point `plugin.py`.
- `plugin.py` — `register(api)`: contributes `maya-scripts/` to the shared
  `maya_launcher_env_bridge` `PluginConfigStore` (same convention every
  other Maya tool plugin here uses). Relies on `plugins/studio/MayaToolkit`
  (for `UkoreMaya.core.Pipeline`'s export commands) and
  `plugins/studio/PublishApi` (for path resolution/versioning) also being
  enabled — not imported directly, just expected on the same merged
  PYTHONPATH once Maya launches. **Also** registers a `CATEGORY_REPO`
  Settings tab (`settings_page.py`, see below) — a UkoreHub-side page, not
  Maya-side, unlike everything else `plugin.py` does.
- `settings_page.py` — `RigPublisherSettingsPage`: the "Repo Studio
  Setting" tab (Repository Setting popup > RigPublisher) — same shape as
  `plugins/studio/ModelPublisher/`'s own `settings_page.py`: lets a studio
  admin pick which of the active repo's declared pipeline **connections**
  this tool should actually publish into, persisted into
  `data/plugins/studio/rig_publisher.json`.
- `maya-scripts/RigPublisher/function.py` — `TOOL_ID = "rig_publisher"`,
  `TICKETS = ["Main", "Proxy", "Hi"]`, `publish(ticket)`: resolves the
  publish root via `PublishApi.repo_paths.get_publish_root(TOOL_ID)` (the
  chosen pipeline connection, already scoped to its `CustomPath`), creates
  the next version folder via `PublishApi.versioning.get_version_directory()`,
  then exports `<ticket>_v<NNN>.ma` (`Pipeline.export_maya_common`) into
  it.
- `maya-scripts/RigPublisher/interface.py` — `MainWindow`
  (`tmlib.ui.interface_template.ToolkitWindow`): same shape as
  `plugins/studio/ModelPublisher/`'s own `interface.py` — ticket list +
  snapshot/publish/open-folder buttons, no custom-path input of any kind
  (removed 2026-07-19, see "What changed" below). `refresh_publish_destination()`
  re-resolves the root/version live as the ticket changes.
- `maya-scripts/RigPublisher/ui.ui` — Qt Designer layout, loaded via
  `importlib.import_module("RigPublisher")` + `__path__[0]/ui.ui`.

## What changed from the original UkorePublisher

Same as `plugins/studio/ModelPublisher/README.md`'s "What changed" section
— publish root now always comes from `PublishApi`'s pipeline-connection
resolution instead of the old `share`/`publish` scene-path convention
(Project Editor also dropped its separate "Set as Pipeline Output..."
action the same day), no more Type selection, and the free-text "Custom
Path" field artists used to type in Maya is gone in favor of
`settings_page.py`'s studio-side picker.

## Working on this plugin

Read/edit only files under this folder unless the change is specifically
about `PublishApi`'s API surface (a genuine cross-plugin task) — see the
`ukorehub-plugin` skill.
