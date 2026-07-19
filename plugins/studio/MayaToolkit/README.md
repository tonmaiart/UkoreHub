# plugins/studio/MayaToolkit/

MayaToolkit — UkoreHub's own vendored Maya scripts and plug-ins (Renamer,
RigBox, WeightPuller, `tmlib`, `UkoreMaya`, and friends, under
`maya-scripts/`), plus compiled plug-ins under `maya-plug-ins/`. Unchanged
internal layout from the original `add-on/MayaToolkit/` (moved to
`plugins/studio/maya_launcher/MayaToolkit/` during the 2026-07-14
consolidation, then split back out to its own top-level plugin here on
2026-07-19 — see `plugins/studio/maya_launcher/README.md` for why).

**UkorePublisher was extracted out of `maya-scripts/UkorePublisher/` on
2026-07-19** into its own top-level plugin, then split again the same day
into three type-specific plugins — `plugins/studio/ModelPublisher/`,
`plugins/studio/RigPublisher/`, `plugins/studio/AnimationPublisher/` — all
built on the new `plugins/studio/PublishApi/` shared library instead of a
single shared UI/publish-path convention. `UkoreMaya/core/menu_utils.py`'s
old single `publisher()` function became three:
`model_publisher()`/`rig_publisher()`/`animation_publisher()`, each calling
`tmlib.core.File.launch("ModelPublisher")`/`"RigPublisher"`/
`"AnimationPublisher"` — `File.launch` resolves by Python module name
(`import <Name>`), not by filesystem nesting, so this works the same way
it always has once each new plugin's own `plugin.py` contributes its
`PYTHONPATH` entry to the bridge (see below).

Like every other Maya tool plugin here, this does **not** launch Maya
itself and has no UI of its own inside UkoreHub — `plugin.py`'s
`register(api)` writes `PYTHONPATH` (`maya-scripts/`) and
`MAYA_PLUG_IN_PATH` (`maya-plug-ins/`) contributions into
`plugins/studio/maya_launcher/`'s shared `maya_launcher_env_bridge`
`PluginConfigStore`, read and merged by that plugin's `open_maya_file`
when it actually launches Maya. No direct import relationship with
`maya_launcher` — just the shared `PluginConfigStore` id convention (see
that plugin's README for the full bridge shape). `RepoToolsStore` (owned
by `maya_launcher`) is what lets a studio admin disable this tool per-repo;
this plugin always contributes unconditionally.

**`plugins/studio/UkoreBrowser/` still depends on this plugin** staying
enabled — it imports `tmlib`/`UkoreMaya` by name rather than vendoring
them itself. See that plugin's README's "External dependencies" section.
