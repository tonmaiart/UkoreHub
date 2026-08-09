# plugins/repo_internal/UkorePlayblast/

Configurable Maya playblast — **entirely a Maya-side tool** (confirmed with
the user 2026-07-19: no UkoreHub desktop UI at all, unlike `MayaPublisher`,
which pairs a Maya package with a Repository Setting tab of its own —
picking Publish Mode). This plugin's own
`plugin.py` only contributes `PYTHONPATH` to the shared
`maya_launcher_env_bridge` so Maya can import its
`maya-scripts/UkorePlayblast/` package — see
`plugins/repo_internal/maya_launcher/README.md`. Replaces UkoreMaya's old
hardcoded "Quick Playblast" (Animation menu), which had no options dialog
at all — resolution, format/codec, quality, frame range, camera, sound,
and show-ornaments were all either hardcoded or implicit. Writes into
whichever folder `cache/plugins/UkoreShot/` has configured for the active
repo, so a playblast immediately shows up in that plugin's video
library/review tab. Renamed from `UkoreShotPlayblast` on 2026-07-20 (id
`ukore_shot_playblast` -> `ukore_playblast`) — see `developer/bug-history/` entries
from that date for the plugin's pre-rename history.

## Flat naming convention

As of 2026-07-20, a playblast lands **flat** in the repo's video root again
— no more `<sequence>/<shot_code>/vNNN/` subfolders (that scheme, from
earlier the same day, is superseded; see "Pre-2026-07-20 shot/version
subfolders" below for what happens to files it already wrote). All the
same information — sequence, shot, which take/pass this is, which output
this is within that take, and the version — now lives entirely in the
**filename** instead:

```
SEQ_ShotCode_Variation_index_version.ext
KBA_KBA030_Blocking_001_v001.mov
```

- **SEQ**/**ShotCode** — parsed off the current scene's basename the same
  way as before (`_SHOT_CODE_PATTERN`, a leading `letters+digits` run —
  `"KBA140_Anim_Layout_v001"` -> `"KBA"` / `"KBA140"`). Falls back to
  sequence `"misc"` + the whole (sanitized) scene basename as the shot
  code if the scene name doesn't parse (untitled scene, or a name that
  doesn't start with that pattern) — a deliberate fallback, not an error,
  so an oddly-named scene still produces a playblast.
- **Variation** — a per-repo choice from the "Playblast Options..."
  dialog's new Variation dropdown: `layout`/`blocking`/`spline` built in
  (`options_store.BUILTIN_VARIATIONS`), plus whatever a repo has added via
  "Add..." (`options_store.add_variation`, saved per-repo — confirmed with
  the user 2026-07-20).
- **index**/**version** — see "Versioning" below. Both, along with
  sequence/shot/variation, are sanitized to letters-and-digits-only
  (`_sanitize_token`) before ever landing in a filename — the stem is
  split on `"_"` into exactly 5 parts by both this plugin's own
  `_FILENAME_PATTERN` and `cache/plugins/UkoreShot/video_naming.py` (the
  desktop-side reader of these same files), so nothing in the first three
  tokens may itself contain an underscore.

### Versioning

Each **exact** `(sequence, shot_code, variation)` triple has its own
independent version counter (confirmed with the user 2026-07-20 — e.g.
`Blocking` can be at `v005` while `Layout` on the same shot is still at
`v002`) — `_matching_versions` scans `video_root`'s top level (not
recursive — this convention has no subfolders of its own) for existing
files matching that exact triple via `_FILENAME_PATTERN`, building
`{version: [index, index, ...]}`.

- **Video** playblast: always a **new** version (`_next_version` = highest
  existing + 1, or `1`), index always `001` — one clip is the whole
  version. As of 2026-08-08, a Video playblast also writes a full-range
  image sequence for the same take — see "Image sequence alongside Video"
  below.
- **Image (Current Frame)** playblast (see "Current-frame image mode"
  below): reuses whichever version **already exists** for that triple
  (`_latest_version`; creates `v001` if this is the first playblast for it
  at all) and takes the next **index** within that version
  (`_next_index`) — confirmed with the user 2026-07-20 that an image
  playblast "adds an index into the same version" rather than starting a
  new one, so a set of stills from one take ends up as `v001` index
  `001`, `002`, `003`... instead of each being its own version.

`_resolve_filename_stem` combines the above into the final stem;
`resolve_destination_path()` (the preview used by the options dialog's
destination label — now a full **file** preview, not just a folder, since
the filename is where all the interesting information lives now) and
`publish_playblast()` both call it, so the preview always matches where
the file actually lands.

### Current-frame image mode

Added 2026-07-20: "Playblast Options..." now has an Output section —
**Video** (existing behavior) or **Image (Current Frame)**. Image mode
captures **only** whatever frame the timeline's playhead is on right now
— not the saved frame range, not the whole timeline turned into an image
sequence — confirmed explicitly with the user ("มันจะเป็นโหมดสำหรับ
Current Frame เลย ไม่ใช่การเอา time slider มาแปลงเป็น image sequence
ทั้งหมด"). `function.py`'s `publish_playblast()` pins
`startTime`/`endTime`/`frame` all to `cmds.currentTime(query=True)` and
calls `cmds.playblast(format="image", compression=<image_format>, ...)`
— frame-range/sound options are ignored in this mode (and disabled in the
dialog, `_on_output_mode_changed`). Maya's `image` format always appends
its own frame-number suffix to the given filename (e.g.
`<stem>.0001.png`) with no documented way to suppress it — this is
undone afterward by `_finalize_single_frame_image`, which globs the
destination folder for whatever Maya actually produced and renames it to
the exact `<stem>.<image_format>` this convention expects, rather than
assuming a specific padding width (not guaranteed stable across Maya
versions).

### Image sequence alongside Video

Added 2026-08-08, part of a broader move toward frame-accurate review
tooling (UkoreShot/BananaSketch) that a video container doesn't give
cheaply. `publish_playblast()`'s Video output branch now runs a *second*
`cmds.playblast(format="image", ...)` over the same range right after the
video capture, writing into `<video_root>/<stem>/<stem>.####.<image_format>`
— a subfolder named exactly after the video's own stem, using whatever
format `image_format_combo` is set to (that field is no longer
Image-Current-Frame-only). No ffmpeg or other new dependency — Maya's own
`format="image"` already writes one numbered file per frame natively when
the range isn't pinned to a single current frame (unlike the
current-frame-image branch above). `_matching_versions`' scan only
inspects `is_file()` entries at `video_root`'s top level, so this
same-stem subfolder is invisible to it — no naming collision, no change
needed there. A failure in this second capture is caught separately and
only logged (`[UkorePlayblast] Image sequence capture failed...`) — it
never invalidates the video already saved by the first call. Known
tradeoff: this doubles viewport capture time for Video mode (two full
passes over the range); not addressed yet.

`cache/plugins/UkoreShot/` (the desktop-side video library/player) does
**not** read these sequence subfolders yet — its library scan is
recursive but filters to `.mov`/`.mp4`/`.avi`, so it harmlessly ignores
the new image files. Teaching the desktop side to actually use them is a
separate, not-yet-scheduled piece.

### Pre-2026-07-20 shot/version subfolders

Playblasts already written under the old `<sequence>/<shot_code>/vNNN/`
scheme are **left exactly where they are** (confirmed with the user
2026-07-20, "ปล่อยไว้เหมือนเดิม") — nothing here migrates or renames them.
They're simply invisible to `_matching_versions`' flat top-level scan (so
they can never collide with a new flat-named file), and
`cache/plugins/UkoreShot/video_naming.py`'s parser treats anything that
doesn't match the new flat convention as unparseable, bucketing it under
"Unknown" in that plugin's filter sidebar rather than erroring or hiding
it.

## Files

- `manifest.json` — plugin id `ukore_playblast`.
- `plugin.py` — `register(api)`: contributes
  `{"PYTHONPATH": {"*": [.../maya-scripts]}}` to the shared
  `maya_launcher_env_bridge` (same convention `MayaPublisher/plugin.py`
  uses for its own package — no changes needed to `maya_launcher` itself,
  it already reads whatever any tool contributes). That's its entire
  UkoreHub-facing surface — pure infrastructure, same "no artist-facing
  behavior or UI of its own" reasoning `maya_launcher/plugin.py`'s own
  `PUBLISH_API_TOOL_ID` comment gives for `PublishApi`.
- `maya-scripts/UkorePlayblast/options_store.py` — `DEFAULT_OPTIONS`
  for any repo that hasn't opened "Playblast Options..." yet. Mostly
  reproduces the old hardcoded `publish_playblast` behavior, except
  `format`/`compression`: the old hardcoded `"qt"`/`"H.264"` values were
  changed to `"avi"`/`""` (uncompressed) on 2026-07-19 after a real
  "Unable to create a movie file" playblast failure — modern Maya on
  Windows has no QuickTime backend at all, so `"qt"` likely never actually
  worked there; `"avi"` needs no external codec framework, and leaving
  compression blank avoids assuming any specific codec is installed
  (applies to `output_mode == "video"` only, see below).
  `get_options`/`set_options`, constructing
  `PluginConfigStore(<active repo's own local clone>/.ukorehub/ukore_playblast.json)`
  straight off disk (same pattern `PublishApi.repo_paths` and
  `PublishApi.tickets` use — Maya's Python has no `PluginAPI` instance)
  under a plain `repo_options: {...}` key — committed to the repo's own git
  history, like `PublishApi`'s ticket storage, since these are team-shared
  playblast defaults, not a personal preference. Previously lived in a
  single shared, cloud-synced `data/plugins/core/ukore_playblast.json`
  (every studio repo's options in one file, keyed
  `"<project_id>:<repo_id>"`) — moved out since that file needs Google
  Cloud Storage access this Maya process doesn't have; see
  `options_store.py`'s `_migrate_from_shared_store` for how an existing
  repo's saved options are carried forward on first access.
  Added 2026-07-20 for the flat naming convention (see above):
  `"variation"` (this repo's currently-selected variation string) and
  `"output_mode"`/`"image_format"` (`"video"` | `"current_frame_image"`,
  and the image format used only in the latter). `BUILTIN_VARIATIONS`
  (`layout`/`blocking`/`spline`) plus `get_variations`/`add_variation`
  manage each repo's own custom variation list separately, under its own
  `repo_variations` key (not mixed into `repo_options`, since it's a list
  a repo builds up over time rather than a single current setting) —
  `add_variation` sanitizes (`_sanitize_token`, letters/digits only,
  duplicated from `function.py`'s identical helper the same reason
  `_repo_key` already was — too small to warrant a shared module) and
  returns the sanitized value actually saved so the dialog can select
  exactly that.
- `maya-scripts/UkorePlayblast/options_dialog.py` —
  `PlayblastOptionsDialog` (`QDialog`, via `tmlib.module.PySide`'s
  version-aware PySide2/PySide6 shim and `tmlib.ui.interface_template
  .get_maya_window` for correct Maya-parented behavior — same Qt access
  pattern `MayaPublisher/maya-scripts/MayaPublisher/interface.py` uses). A
  new "Naming / Output" group (added 2026-07-20, sits above Resolution
  since it's now core naming metadata, not a minor detail) holds
  `variation_combo` (`options_store.get_variations`) + an "Add..." button
  (`_on_add_variation` -> `QInputDialog.getText` -> `options_store
  .add_variation` -> `_reload_variation_combo`, selecting the new value),
  and `output_video_radio`/`output_image_radio` (mutually exclusive via a
  `QButtonGroup`) + `image_format_combo` — toggling to Image (Current
  Frame) disables `format_box`/`frame_range_box`/`sound_check` via
  `_on_output_mode_changed` (none of them apply to a single-current-frame
  capture) and enables `image_format_combo` instead. `_FORMATS` dropped
  its old third `"image"` choice (see the README's "Current-frame image
  mode" section for why a whole-timeline image sequence via the generic
  format field was the wrong shape for what got asked for). Also still:
  Resolution (render settings vs. custom width/height), format/compression,
  quality%, viewport-scale%, frame range (current timeline vs. custom
  start/end), camera (blank = active viewport), sound, show ornaments —
  the exact same field set the removed desktop settings page had, just
  living in Maya now. A `destination_label` at the top
  (`_refresh_destination_label`) shows the full file path
  `function.resolve_destination_path()` currently resolves to for the
  active repo/scene/options (a full file preview since 2026-07-20, not
  just a folder — see "Flat naming convention" above), refreshed on open,
  after every playblast, and now live as `variation_combo`/the output-mode
  radios/`format_combo`/`image_format_combo` change (those all feed the
  filename directly now). A "Playblast" button sits in the button row
  alongside OK/Cancel (`QDialogButtonBox.ActionRole`, since it doesn't
  close the dialog) — `_on_playblast` saves the current widget values via
  the shared `_collect_options()` (also used by `_on_accept`) and calls
  `function.publish_playblast()` directly, so changes can be test-playblast'd
  without closing the dialog first. Saves on OK via `options_store.set_options`;
  `show()` is the module-level entry point `menu_utils.py`'s
  `playblast_options()` calls.
- `maya-scripts/UkorePlayblast/function.py` — `publish_playblast()`,
  what `plugins/repo_internal/MayaToolkit`'s UkoreMaya menu now calls (see that
  plugin's `menu_utils.py`) instead of its own now-removed hardcoded
  version, and what `options_dialog.py`'s "Playblast" button calls
  directly — a single entry point for both Video and Image (Current
  Frame) output, branching on `options["output_mode"]` (see "Current-frame
  image mode" above). Resolves the active repo via
  `PublishApi.repo_paths.get_active_repo()`, the video root via
  `_resolve_video_root` (mirrors
  `cache/plugins/UkoreShot/video_path_store.py`'s `resolve_video_root`
  exactly — reads `data/plugins/core/ukore_shot.json` and
  `PublishApi.repo_paths.get_custom_paths`/`get_custom_path` directly off
  disk, no shared "bridge" file needed for this), this repo's options via
  `options_store.get_options`, and the destination filename via
  `_resolve_filename_stem` (see "Flat naming convention" above — no more
  per-shot subfolder, `os.makedirs` now just ensures the flat `video_root`
  itself exists). Video mode's branch also runs a second `cmds.playblast()`
  pass into a `<stem>/` image-sequence subfolder — see "Image sequence
  alongside Video" above. `resolve_destination_path()` exposes just the
  active-repo/scene/options/filename resolution (no `os.makedirs`, no
  playblast) for `options_dialog.py`'s destination label. Prints
  `[UkorePlayblast]`-prefixed progress lines to Maya's Script
  Editor/console (start, resolved destination folder + filename, options
  in use, saved path or failure reason) so a playblast run — whether from
  the Animation menu or the dialog's Playblast button — is traceable
  without opening the dialog.

## MayaToolkit integration

`plugins/repo_internal/MayaToolkit/maya-scripts/UkoreMaya/core/menu_utils.py` has
two functions for this tool: `playblast()` (lazily imports and calls this
plugin's `function.py`, the same lazy-import-a-separate-package pattern
`maya_publisher()` already uses there for its own separate plugin) and
`playblast_options()` (lazily imports and calls
`options_dialog.show()`). `plugins/repo_internal/MayaToolkit/maya-plug-ins/ukoreMaya.py`
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
