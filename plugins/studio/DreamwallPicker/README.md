# plugins/studio/DreamwallPicker/

Vendored copy of DreamWall Animation's [DwPicker](https://github.com/DreamWall-Animation) for Maya — a
picker/rigging-control UI tool. Self-contained (no dependency on
MayaToolkit's `tmlib`/`UkoreMaya`, unlike `UkoreBrowser`) — only needs
`maya.cmds` and PySide, both provided by Maya itself.

Started as its own `add-on/DreamwallPicker/`, was folded into
`plugins/studio/maya_launcher/DreamwallPicker/` as one of 7 nested tools
during the 2026-07-14 consolidation, then split back out to this top-level
plugin on 2026-07-19 — see `plugins/studio/maya_launcher/README.md` for why.

- `manifest.json` / `plugin.py` — standard plugin registration (see
  `plugins/README.md`). `plugin.py` only contributes its `maya-scripts/`
  folder to `plugins/studio/maya_launcher/`'s shared
  `maya_launcher_env_bridge` `PluginConfigStore` PYTHONPATH bridge (same
  convention every other Maya tool plugin here uses, e.g.
  `plugins/studio/AdvancedSkeleton/plugin.py`) — no file opener, no UI of
  its own inside UkoreHub. No direct import relationship with
  `maya_launcher` — just the shared `PluginConfigStore` id convention.
- `maya-scripts/dwpicker/` — the vendored package as-is, unmodified.
  `dwpicker.show()` (in `dwpicker/__init__.py`) is the entry point; called
  from the UkoreMenu in `plugins/studio/MayaToolkit/maya-scripts/UkoreMaya/`'s
  Maya menu, not launched by this plugin itself.

## Working on this plugin

Read/edit only files under this folder — see `plugins/README.md`'s
plugin-scoping note (and the `ukorehub-plugin` skill). This is third-party
vendored code: prefer not to modify `dwpicker/` internals directly unless
there's a specific reason (upstream: https://github.com/DreamWall-Animation).
