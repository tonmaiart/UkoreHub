# plugins/studio/AdvancedSkeleton/

AdvancedSkeleton — a vendored Maya rigging toolset, unchanged internal
layout from the original `add-on/AdvancedSkeleton/` (moved to
`plugins/studio/maya_launcher/AdvancedSkeleton/` during the 2026-07-14
consolidation, then split back out to its own top-level plugin here on
2026-07-19 — see `plugins/studio/maya_launcher/README.md` for why).

Like every other Maya tool plugin here, this does **not** launch Maya
itself and has no UI of its own inside UkoreHub — `plugin.py`'s
`register(api)` only writes a `PYTHONPATH` contribution (pointing at this
folder's `maya-scripts/`) into `plugins/studio/maya_launcher/`'s shared
`maya_launcher_env_bridge` `PluginConfigStore`, read and merged by that
plugin's `open_maya_file` when it actually launches Maya. No direct import
relationship with `maya_launcher` — just the shared `PluginConfigStore` id
convention (see that plugin's README for the full bridge shape).
`RepoToolsStore` (owned by `maya_launcher`) is what lets a studio admin
disable this tool per-repo; this plugin always contributes unconditionally.
