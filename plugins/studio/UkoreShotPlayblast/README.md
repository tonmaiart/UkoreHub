# plugins/studio/UkoreShotPlayblast/

Configurable Maya playblast — **entirely a Maya-side tool** (confirmed with
the user 2026-07-19: no UkoreHub desktop UI at all, unlike
`RigPublisher`/`ModelPublisher`/`AnimationPublisher`, which each pair a
Maya package with their own Repository Setting tab). This plugin's own
`plugin.py` only contributes `PYTHONPATH` to the shared
`maya_launcher_env_bridge` so Maya can import its
`maya-scripts/UkoreShotPlayblast/` package — see
`plugins/studio/maya_launcher/README.md`. Replaces UkoreMaya's old
hardcoded "Quick Playblast" (Animation menu), which had no options dialog
at all — resolution, format/codec, quality, frame range, camera, sound,
and show-ornaments were all either hardcoded or implicit. Writes into
whichever folder `plugins/studio/UkoreShot/` has configured for the active
repo, so a playblast immediately shows up in that plugin's video
library/review tab.

## Files

- `manifest.json` — plugin id `ukore_shot_playblast`.
- `plugin.py` — `register(api)`: contributes
  `{"PYTHONPATH": {"*": [.../maya-scripts]}}` to the shared
  `maya_launcher_env_bridge` (same convention `RigPublisher/plugin.py`
  uses for its own package — no changes needed to `maya_launcher` itself,
  it already reads whatever any tool contributes). That's its entire
  UkoreHub-facing surface — pure infrastructure, same "no artist-facing
  behavior or UI of its own" reasoning `maya_launcher/plugin.py`'s own
  `PUBLISH_API_TOOL_ID` comment gives for `PublishApi`.
- `maya-scripts/UkoreShotPlayblast/options_store.py` — `DEFAULT_OPTIONS`
  for any repo that hasn't opened "Playblast Options..." yet. Mostly
  reproduces the old hardcoded `publish_playblast` behavior, except
  `format`/`compression`: the old hardcoded `"qt"`/`"H.264"` values were
  changed to `"avi"`/`""` (uncompressed) on 2026-07-19 after a real
  "Unable to create a movie file" playblast failure — modern Maya on
  Windows has no QuickTime backend at all, so `"qt"` likely never actually
  worked there; `"avi"` needs no external codec framework, and leaving
  compression blank avoids assuming any specific codec is installed. Plus
  `get_options`/`set_options`, constructing
  `PluginConfigStore(.../data/plugins/studio/ukore_shot_playblast.json)`
  straight off disk (same pattern `PublishApi.repo_paths` and
  `UkoreBrowser/core/repo_context.py` use — Maya's Python has no
  `PluginAPI` instance) under `repo_options: {"<project_id>:<repo_id>": {...}}`.
- `maya-scripts/UkoreShotPlayblast/options_dialog.py` —
  `PlayblastOptionsDialog` (`QDialog`, via `tmlib.module.PySide`'s
  version-aware PySide2/PySide6 shim and `tmlib.ui.interface_template
  .get_maya_window` for correct Maya-parented behavior — same Qt access
  pattern `RigPublisher/maya-scripts/RigPublisher/interface.py` uses).
  Resolution (render settings vs. custom width/height), format/compression,
  quality%, viewport-scale%, frame range (current timeline vs. custom
  start/end), camera (blank = active viewport), sound, show ornaments —
  the exact same field set the removed desktop settings page had, just
  living in Maya now. Saves on OK via `options_store.set_options`; `show()`
  is the module-level entry point `menu_utils.py`'s `playblast_options()`
  calls.
- `maya-scripts/UkoreShotPlayblast/function.py` — `publish_playblast()`,
  what `plugins/studio/MayaToolkit`'s UkoreMaya menu now calls (see that
  plugin's `menu_utils.py`) instead of its own now-removed hardcoded
  version. Resolves the active repo via `PublishApi.repo_paths.get_active_repo()`,
  the video destination folder via `_resolve_video_root` (mirrors
  `plugins/studio/UkoreShot/video_path_store.py`'s `resolve_video_root`
  exactly — reads `data/plugins/studio/ukore_shot.json` and
  `PublishApi.repo_paths.get_custom_paths`/`get_custom_path` directly off
  disk, no shared "bridge" file needed for this), and this repo's options
  via `options_store.get_options`. Output filename is
  `<scene_basename>_<YYYYMMDD_HHMMSS>` (extension added by Maya per the
  chosen format) — deliberately timestamped rather than overwriting the
  previous playblast like the old hardcoded version did, since these files
  now feed UkoreShot's browsable history.

## MayaToolkit integration

`plugins/studio/MayaToolkit/maya-scripts/UkoreMaya/core/menu_utils.py` has
two functions for this tool: `playblast()` (lazily imports and calls this
plugin's `function.py`, the same lazy-import-a-separate-package pattern
`rig_publisher()`/`model_publisher()` already use there for their own
separate plugins) and `playblast_options()` (lazily imports and calls
`options_dialog.show()`). `plugins/studio/MayaToolkit/maya-plug-ins/ukoreMaya.py`
wires both into the Animation menu — "Playblast" plus a Maya-native
option-box (`cmds.menuItem(optionBox=True, ...)`, the small square icon
immediately after the main item, matching Maya's own "Playblast Options"/
"Export Options" convention) for "Playblast Options...". The Animation menu
itself stays owned by `MayaToolkit` — there is deliberately only one Ukore
Studio Tool menu, not one per tool plugin.

**Working here:** stay inside this folder — the one legitimate cross-plugin
touch this feature needed (wiring `MayaToolkit`'s menu item to both
functions here) is documented in that plugin's own history, not duplicated
here.
