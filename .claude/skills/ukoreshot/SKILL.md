---
name: ukoreshot
description: Working reference for plugins/studio/UkoreShot/ (C:\Tonmai\UkoreHub) — UkoreHub's per-repo playblast video library/review plugin. Use this whenever a task names UkoreShot specifically, or targets a path under plugins/studio/UkoreShot/ (its player/drawing/comment UI, its video-naming/filter logic, its icons, or its own bug-history) — before the general ukorehub-plugin skill's folder-scoping rule, since this skill covers UkoreShot's own internal subfolder split (core/interface/images/bug-history) that the general skill doesn't know about. Also load this for plugins/studio/UkorePlayblast/ tasks that touch the shared naming convention between the two plugins.
---

# UkoreShot — structure and domain knowledge

`plugins/studio/UkoreShot/` is a normal `plugins/studio/<Name>/` plugin
(the `ukorehub-plugin` skill's "stay inside your plugin folder" rule
applies against every *other* plugin as always), but internally it's
split into subfolders — read only the one your task needs, same
token-budget reasoning as staying inside the plugin at all:

- `core/` — non-UI logic (video-root path resolution, comment JSON
  persistence, playblast filename parsing). No PySide6 here.
- `interface/` — every PySide6 widget/page/dialog.
- `images/` — this plugin's own icon PNGs (see "Icons" below — this is a
  deliberate exception to the rest of the app's `data/icons/` convention).
- `bug-history/` — bugs fixed specifically in this plugin's own code,
  going forward from 2026-07-21 (older UkoreShot bugs are still at the
  repo-root `bug-history/` — see that folder's README for the pointers).

**Read that subfolder's own `README.md` before opening its individual
files** — each is a full, current description of what's inside, written
so you don't need to open every file to place them in context. The
top-level `plugins/studio/UkoreShot/README.md` is now a short index/rule
page, not the content itself — start there only to decide which subfolder
you need, then go read that subfolder's README.

`manifest.json`/`plugin.py`/`__init__.py` stay at the plugin's top level
(outside all four subfolders) — the plugin loader
(`core/extensibility/loader.py`) requires both directly there. Everything
else is free to live wherever makes sense internally, since `plugin.py`
only ever reaches `interface/`/`core/` through normal absolute Python
imports (`from plugins.studio.UkoreShot.interface.video_library_page import UkoreShotPage`,
etc.), never anything path-based.

## The `core` naming collision

Two files import a bare `from core...`:
`core/comment_store.py`'s `from core.store import LocalConfigStore` and
`interface/draw_overlay.py`'s `from core.extensibility import debug_log`.
**Both mean the app's own top-level `core/` package**
(`C:\Tonmai\UkoreHub\core\`), never this plugin's sibling `core/`
subfolder — absolute imports resolve from the repo root regardless of
where the importing file lives, so this is only confusing to a human
reader, never a runtime bug. Don't "fix" one of these imports to be
relative or plugin-scoped; it's already correct.

## Companion plugin: UkorePlayblast (Maya-side, separate codebase)

`plugins/studio/UkorePlayblast/` is the Maya-side tool that writes the
video files this plugin's library reads — a completely separate Python
environment (Maya's own interpreter, not UkoreHub's desktop app), so
**nothing in either plugin imports from the other**. Where both sides need
to agree on something, it's duplicated deliberately rather than shared:

- **Flat naming convention** — `SEQ_ShotCode_Variation_index_version.ext`
  (e.g. `KBA_KBA030_Blocking_001_v001.mov`), written by
  `UkorePlayblast/maya-scripts/UkorePlayblast/function.py`'s
  `_FILENAME_PATTERN`/`_resolve_filename_stem`, read by this plugin's own
  `core/video_naming.py`'s `_FILENAME_PATTERN`/`parse_video_filename` —
  the two regexes are independent, kept in sync by hand. See
  `UkorePlayblast/README.md`'s "Flat naming convention" section for the
  full scheme (sequence/shot/variation/index/version semantics, the
  per-variation independent version counters, the current-frame image
  mode). A video whose filename doesn't match (most likely a
  pre-2026-07-20 playblast still sitting in its own old
  `<sequence>/<shot_code>/vNNN/` subfolder, left alone there by design —
  not migrated) shows up as `"Unknown"` in every naming-derived filter
  category in `interface/filter_sidebar.py`, never hidden or an error.
- **Video root resolution** — both sides independently read
  `data/plugins/studio/ukore_shot.json`'s `repo_video_custom_path` off
  disk (this plugin's own `core/video_path_store.py`, and
  `UkorePlayblast`'s `function.py`'s `_resolve_video_root`) — the
  "construct the store straight off disk" pattern this whole codebase
  uses for Maya-side/desktop-side pairs with no shared `api` handle.

## Comment data shape

`core/comment_store.py`'s sidecar JSON (`<video>.ukoreshot.json`):
`{"frames": {"<frame_index>": {"strokes": [...], "comments": [{"id", "author", "text", "timestamp"}], "text_boxes": [...]}}}`.
`"comments"` (a list — multiple users can comment on the same frame,
Facebook-style, each individually deletable, see `interface/comment_thread.py`)
replaced an older single `"note"` string field on 2026-07-20; a frame
saved before then may still only have `"note"` —
`interface/player_widget.py`'s `PlayerWidget._migrate_comments` reads that
into a one-item comments list for display, but `comment_store.py` itself
never rewrites old files — only a fresh save replaces `"note"` with
`"comments"` for that one frame entry.

## Two faces of `PlayerWidget`

`interface/player_widget.py`'s `PlayerWidget(show_edit_tools=...)` is used
two ways, and almost every feature question about this plugin comes down
to which one applies:

- `show_edit_tools=False` — the inline preview in
  `interface/video_library_page.py`'s `UkoreShotPage`. Playback +
  read-only comment/stroke display only (`ReadOnlyCommentOverlay`), no
  drawing toolbox, no editable comment thread. Has its own
  `edit_comment_button` (emits `editCommentRequested`) that opens...
- `show_edit_tools=True` — the full interactive editor, only ever embedded
  by `interface/edit_video_dialog.py`'s `EditVideoDialog` (a modal popped
  up by the button above). Drawing toolbox (`DrawOverlay`), the
  Facebook-style `CommentThread`, undo/redo — everything that actually
  writes to `comment_store.py`.

Both modes share the transport controls, frame-number HUD, comment
sidebar, and keyboard shortcuts — see `interface/README.md`'s
`player_widget.py` entry for the exact widget-by-widget breakdown.

## Icons

This plugin's icons live in its own `images/` folder, **not** the shared
`data/icons/` every other plugin uses (see root `CLAUDE.md`'s "Project
layout") — confirmed with the user 2026-07-21 as a deliberate exception.
`interface/player_widget.py` resolves `_ICONS_DIR` as
`Path(__file__).resolve().parents[1] / "images"`. Never open the PNGs
themselves speculatively (same "don't open image directories" reasoning
root `CLAUDE.md` gives for `data/thumbnails/` etc.) — check
`player_widget.py`'s `_..._ICON_PATH` constants instead, or
`images/README.md`'s file list.

## Bug history

Check `bug-history/README.md`'s index first (plugin-local, going forward
from 2026-07-21). If it doesn't cover what you're touching, that same
README points at three repo-root `bug-history/` entries from before this
folder existed — a native-video-widget mouse-event bug, a
draw/text-tool-simultaneously bug, and a Custom-Path leading-slash bug
shared with `UkorePlayblast`. After fixing any real bug here, add a new
entry to `bug-history/README.md`'s index (or the repo-root one instead, if
the "Lesson" is a generic Qt/Python gotcha rather than something specific
to this plugin's own architecture — see that README's own guidance on the
distinction).
