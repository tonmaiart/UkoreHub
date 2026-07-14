# add-on/DreamwallPicker/

Vendored copy of DreamWall Animation's [DwPicker](https://github.com/DreamWall-Animation) for Maya — a
picker/rigging-control UI tool. Self-contained (no dependency on
MayaToolkit's `tmlib`/`UkoreMaya`, unlike `UkoreBrowser`) — only needs
`maya.cmds` and PySide, both provided by Maya itself.

- `manifest.json` / `plugin.py` — standard add-on registration (see
  `add-on/README.md`). `plugin.py` only contributes its `maya-scripts/`
  folder to the shared `maya_launcher_env_bridge` PYTHONPATH bridge (same
  convention as `add-on/AdvancedSkeleton/plugin.py`) — no file opener or
  repo-addon panel.
- `maya-scripts/dwpicker/` — the vendored package as-is, unmodified.
  `dwpicker.show()` (in `dwpicker/__init__.py`) is the entry point; called
  from the UkoreMenu in `add-on/MayaToolkit/maya-scripts/UkoreMaya/`'s Maya
  menu, not launched by this add-on itself.

## Working on this add-on

Read/edit only files under this folder — see `add-on/README.md`'s
add-on-scoping note (and the `ukorehub-addon` skill). This is third-party
vendored code: prefer not to modify `dwpicker/` internals directly unless
there's a specific reason (upstream: https://github.com/DreamWall-Animation).
