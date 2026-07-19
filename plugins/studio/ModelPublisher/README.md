# plugins/studio/ModelPublisher/

Maya-side tool that publishes the active Model scene (FBX + a raw Maya
Ascii copy) into a versioned folder. Split out of the original
`UkorePublisher` plugin's "Model" branch on 2026-07-19, alongside
`RigPublisher`/`AnimationPublisher` and the new `PublishApi` shared
library — see `plugins/studio/PublishApi/README.md` and
`plugins/studio/maya_launcher/README.md` for the bridge convention this
follows. Has its own dedicated UI now (no "Type" list — this plugin only
ever publishes Model) instead of sharing one UI across every publish type
the way `UkorePublisher` used to.

## Files

- `manifest.json` — plugin id `model_publisher`, entry point `plugin.py`.
- `plugin.py` — `register(api)`: contributes `maya-scripts/` to the shared
  `maya_launcher_env_bridge` `PluginConfigStore` (same convention every
  other Maya tool plugin here uses). Relies on `plugins/studio/MayaToolkit`
  (for `UkoreMaya.core.Pipeline`'s export commands) and
  `plugins/studio/PublishApi` (for path resolution/versioning) also being
  enabled — not imported directly, just expected on the same merged
  PYTHONPATH once Maya launches. **Also** registers a `CATEGORY_REPO`
  Settings tab (`settings_page.py`, see below) — a UkoreHub-side page, not
  Maya-side, unlike everything else `plugin.py` does.
- `settings_page.py` — `ModelPublisherSettingsPage`: the "Repo Studio
  Setting" tab (Repository Setting popup > ModelPublisher) — lets a studio
  admin pick which of the active repo's declared pipeline **connections**
  ("Connect Pipeline Input Path...", a `{project_id, repo_id,
  custom_path_id}` pointing at a specific `CustomPath` inside a target
  repo — see `plugins/studio/project_editor/pipeline_store.py`) this tool
  should actually publish into. Falls back to "the repo's only declared
  connection" automatically when there's exactly one, so a repo only
  needs an explicit choice here once it has more than one. Persists the
  choice into this plugin's own `PluginConfigStore`
  (`data/plugins/studio/model_publisher.json`, key
  `"repo_publish_target"`), which
  `PublishApi.repo_paths.get_publish_root("model_publisher")` reads back
  on the Maya side (see that plugin's README). Same
  self-resolving-active-repo `refresh()` pattern as
  `interface/settings/browser_links_settings_page.py`.
- `maya-scripts/ModelPublisher/function.py` — `TOOL_ID = "model_publisher"`,
  `TICKETS = ["Main", "Proxy", "Hi"]`, `publish(ticket)`: resolves the
  publish root via `PublishApi.repo_paths.get_publish_root(TOOL_ID)` (the
  chosen pipeline connection, already scoped to its `CustomPath` — see
  `settings_page.py` above), creates the next version folder via
  `PublishApi.versioning.get_version_directory()`, then exports
  `<ticket>_v<NNN>.fbx` (`Pipeline.export_fbx_common`) and
  `<ticket>_v<NNN>.ma` (`Pipeline.export_maya_common`) into it.
- `maya-scripts/ModelPublisher/interface.py` — `MainWindow`
  (`tmlib.ui.interface_template.ToolkitWindow`): ticket list, snapshot
  button, publish/open-folder buttons. **No custom-path input of any
  kind** — removed 2026-07-19 alongside adding `settings_page.py` above;
  the artist just picks a ticket, everything else is already decided by
  the studio in UkoreHub. `refresh_publish_destination()` re-resolves the
  root and next version live as the ticket changes, showing a clear error
  message from `PublishApi` (no active repo / no pipeline connection
  declared / ambiguous choice with nothing picked yet / target repo not
  cloned) instead of a blank or stale destination.
- `maya-scripts/ModelPublisher/ui.ui` — Qt Designer layout, loaded by
  `tmlib.ui.interface_template.ToolkitWindow` via
  `importlib.import_module("ModelPublisher")` + `__path__[0]/ui.ui` (same
  convention `plugins/studio/UkoreBrowser/`'s own `ui.ui` uses).

## What changed from the original UkorePublisher

- Publish root: used to come from string-swapping `.../share/...` for
  `.../publish/...` in the current scene's own file path
  (`UkoreMaya/core/Logic.py`'s `convert_to_publish_path`). Now it's always
  `PublishApi.repo_paths.get_publish_root("model_publisher")` — the active
  repo's declared pipeline connection in Project Editor, scoped to a
  specific `CustomPath` this plugin's own Repo Studio Setting tab picked.
  (Project Editor also dropped its separate "Set as Pipeline Output..."
  action the same day — see `plugins/studio/project_editor/README.md`.)
- "Type" selection is gone — this plugin only ever publishes Model, so
  there's no type list, just the ticket list.
- The free-text "Custom Path" field artists used to type in Maya (added
  2026-07-19, removed the same day) is gone — replaced by
  `settings_page.py`'s studio-side picker, since the whole point of
  `CustomPath` is to be a small, curated, studio-declared catalog
  (`plugins/studio/project_editor`'s "Custom Paths" tab), not something an
  artist free-types per publish.

## Working on this plugin

Read/edit only files under this folder unless the change is specifically
about `PublishApi`'s API surface (a genuine cross-plugin task) — see the
`ukorehub-plugin` skill.
