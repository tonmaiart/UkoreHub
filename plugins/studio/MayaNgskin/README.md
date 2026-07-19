# plugins/studio/MayaNgskin/

MayaNgSkin — vendored ngSkinTools2 skin-weighting toolset for Maya
(`maya-scripts/` Python package plus per-Maya-version compiled
`.mll` plug-ins under `maya-plug-ins/<version>/`). Unchanged internal
layout from the original `add-on/MayaNgskin/` (moved to
`plugins/studio/maya_launcher/MayaNgskin/` during the 2026-07-14
consolidation, then split back out to its own top-level plugin here on
2026-07-19 — see `plugins/studio/maya_launcher/README.md` for why).

Like every other Maya tool plugin here, this does **not** launch Maya
itself and has no UI of its own inside UkoreHub — `plugin.py`'s
`register(api)` writes a `PYTHONPATH` contribution (this folder's
`maya-scripts/`) plus a **versioned** `MAYA_PLUG_IN_PATH` contribution
(one entry per `maya-plug-ins/<version>/` subfolder found on disk — Maya's
own `Program.version` selects which one actually applies at launch, since
`ngSkinTools2.mll` ships one build per Maya version, unlike this folder's
other flat-PYTHONPATH siblings) into
`plugins/studio/maya_launcher/`'s shared `maya_launcher_env_bridge`
`PluginConfigStore`, read and merged by that plugin's `open_maya_file`
when it actually launches Maya. No direct import relationship with
`maya_launcher` — just the shared `PluginConfigStore` id convention (see
that plugin's README for the full bridge shape). `RepoToolsStore` (owned
by `maya_launcher`) is what lets a studio admin disable this tool per-repo;
this plugin always contributes unconditionally.
