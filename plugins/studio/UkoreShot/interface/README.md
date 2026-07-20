# plugins/studio/UkoreShot/interface/

Every PySide6 widget/page/dialog for the UkoreShot plugin — no data
persistence or path-resolution logic lives here directly, that's
`../core/` (imported as `from plugins.studio.UkoreShot.core import ...`).
Split out from the plugin's flat file layout on 2026-07-21 — see the
top-level `../README.md`'s "Structure" section for the full rule on
reading only the subfolder a task actually needs.

**Naming note:** `from core.X import Y` anywhere in this folder (e.g.
`draw_overlay.py`'s `from core.extensibility import debug_log`) always
means the app's own **top-level** `core/` package
(`C:\Tonmai\UkoreHub\core\`), never this plugin's sibling `../core/`
folder — see `../core/README.md`'s naming note for why that's always
unambiguous despite the shared name.

## Files

- `repo_video_settings_page.py` — `RepoVideoSettingsPage`, the
  `CATEGORY_REPO` Settings tab. Same self-resolving-active-repo `refresh()`
  + "list of choices, auto-use if there's only one" pattern as
  `plugins/studio/RigPublisher/settings_page.py`'s
  `RigPublisherSettingsPage`, just pointed at `custom_paths` instead of
  `pipeline_inputs` (via `../core/video_path_store.py`).
- `video_library_page.py` — `UkoreShotPage`, the section's top-level
  widget, plus `_VideoCard`. `PlayerWidget(show_edit_tools=False)` (top
  half — `content_layout` gives `player_panel`/`library_panel` equal
  `stretch=1` so the page always splits 50/50) handles plain playback for
  whichever video is selected. The "Edit Comment" button used to live in
  this page's own `player_panel`, right underneath the player — moved
  *inside* `PlayerWidget` itself (still view-mode only) on 2026-07-20, as
  a square icon button next to Show/Hide Comments, so this page now just
  connects to `player_widget.editCommentRequested` and opens
  `EditVideoDialog(self._selected_card.video_path, self)` — no button of
  its own anymore. Note the inline `PlayerWidget` here already shows a
  *read-only* rendering of each frame's comments plus the same right-hand
  comment sidebar since 2026-07-20 (see `player_widget.py`'s own entry) —
  `EditVideoDialog` is only needed to actually *add/edit* a comment now,
  not merely to see one.

  Bottom half (`library_panel`) is `filter_sidebar` (a `FilterSidebar` —
  see that file, added 2026-07-20) on the left, next to `library_content`
  on the right: a `controls_row` (Refresh, then the four sort buttons —
  `sort_az_button`/`sort_za_button`/`sort_oldest_button`/
  `sort_newest_button`, one exclusive `QButtonGroup`, `_sort_videos`
  applies whichever's checked — then, right-aligned via a stretch, the two
  view-mode buttons `view_small_button`/`view_large_button`, another
  exclusive `QButtonGroup` picking a `_CARD_SIZES` preset), then the same
  vertically-scrolling wrapping `cards_layout` grid of `_VideoCard`s as
  before (`FlowLayout`, `flow_layout.py`, not a plain box layout, so cards
  wrap onto new rows and the grid grows downward — built via
  `interface/shared/widget_helpers.wrap_scrollable`, the **app's**
  top-level `interface/` package again, not this folder — with the
  horizontal scrollbar forced off, `cards_scroll` given `stretch=1`).
  `_VideoCard` now takes `card_width`/`thumbnail_height` as constructor
  args (one of `_CARD_SIZES["small"]`/`["large"]`, chosen by the view-mode
  buttons) instead of hard-coded module constants, so switching the toggle
  rebuilds the grid at a different size.

  `_reload_videos` scans `resolve_video_root(...)` (`../core/video_path_store.py`)
  recursively for every `.mov`/`.mp4`/`.avi` file — a video flat-named
  under UkorePlayblast's 2026-07-20 naming convention lives directly in
  the video root, but an older playblast from before that date may still
  sit nested under its own `<sequence>/<shot_code>/vNNN/` subfolder (left
  alone there per the user's own decision — see `UkorePlayblast/README.md`),
  and both need to show up here. For each video it also caches
  `video_naming.parse_video_filename(video_path)` (`../core/video_naming.py`,
  `None` for anything that doesn't match the convention — a legacy nested
  file, most likely) in `_parsed_by_video`, and
  `comment_store.list_commenters(video_path)` (`../core/comment_store.py`)
  in `_commenters_by_video` — both consulted by `_video_matches_filters`
  and by `_collect_filter_values` (which feeds
  `filter_sidebar.set_available_values`). The old `filter_combo`
  (top-level-sequence-only, "All" + a flat list) is gone entirely,
  replaced by `filter_sidebar`'s own Sequence category, which is exactly
  as capable plus five more categories. `_apply_filter` (now no-argument,
  triggered by `filter_sidebar.filtersChanged` or either button group)
  rebuilds the card grid from `_all_videos` filtered through
  `_video_matches_filters` (AND across categories, OR within one — see
  `filter_sidebar.py`'s own docstring) and search text, then sorted via
  `_sort_videos`. `_format_filter_value` is the single place index/version
  get their zero-padded display form (`"003"`/`"v001"`, matching how they
  actually look in the filename) — used identically by both
  `_collect_filter_values` (building the choice list) and
  `_video_matches_filters` (matching a selection against it), so the two
  can never disagree on formatting. A video that doesn't parse
  (`_parsed_by_video[path] is None`) contributes `"Unknown"` to every
  naming-derived filter category rather than being excluded from
  filtering or hidden from the grid.

  Player-on-top/library-below since 2026-07-20, replacing a left-column
  vertical list from earlier the same day (which itself had just replaced
  a plain `QListWidget` IconMode list that rendered badly — overlapping
  thumbnails, cut-off text). A single-row horizontal filmstrip
  (`QHBoxLayout` + horizontal scroll) was tried first for the
  player-on-top layout and replaced with the wrapping grid the same day,
  confirmed with the user. Each `_VideoCard` (`QFrame`, object name
  `videoCard`, styled via `core/theme.py`'s `QFrame#videoCard` rules — the
  app's top-level `core/theme.py`, same card-with-QSS-plus-hand-painted-
  thumbnail idiom `interface/login/repo_picker.py`'s `_RepoCard`
  established) paints its best-effort thumbnail (`thumbnail_loader.py`)
  fill-cropped into a fixed-height top strip, with the video's path
  relative to the video root (filename bold, parent folder secondary/gray)
  underneath as normal child labels. Implements the standard
  `set_repo(project, repo, workspace_root)` page protocol
  (`interface/main_window.py`'s `_apply_to_current_page`).
- `filter_sidebar.py` — `FilterSidebar`, added 2026-07-20: the library's
  left-hand filter panel, one multi-select `QListWidget` per category
  (Sequence, Shot Name, Variation, Index, Version, Commented By —
  `_CATEGORIES`) inside a `wrap_scrollable` column, plus a `search_edit`
  free-text box above them. Selecting several values within one category
  is OR; selecting across categories is AND — this widget only exposes
  the raw state (`selected_values(category)`, `search_text()`) and a
  single `filtersChanged` signal, `video_library_page.py`'s
  `_video_matches_filters` is what actually combines them.
  `set_available_values(values_by_category)` rebuilds every list from
  scratch (called after every `_reload_videos()` rescan) while preserving
  selection for values that still exist, so a Refresh doesn't silently
  clear an active filter.
- `flow_layout.py` — `FlowLayout`, Qt's well-known "Flow Layout" `QLayout`
  recipe (packs children left-to-right, wraps to a new row on overflow,
  `heightForWidth`-driven so a `QScrollArea(widgetResizable=True)` around
  it grows/scrolls vertically). Generic — no UkoreShot-specific code in it
  — reused as-is by `video_library_page.py`'s card grid.
- `thumbnail_loader.py` — `ThumbnailLoader`: one hidden `QMediaPlayer` +
  `QVideoSink` pair, processed one video at a time, grabs the first
  decodable frame as a `QPixmap` for the list icon. Best-effort — a video
  it can't decode a frame from just shows with no icon, nothing crashes.
- `player_widget.py` — `PlayerWidget` + `_VideoSurface` + `_FrameNumberOverlay`
  + `_CommentAwareSlider` + `_VideoStack`:
  `QMediaPlayer` + `_VideoSurface` (a plain `QWidget`, not `QVideoWidget` —
  see its own docstring and the root
  `bug-history/2026-07-20-draw-overlay-native-video-widget.md`, which
  covers both root causes below in full — this plugin's own
  `../bug-history/README.md` points at it too;
  `QVideoWidget` renders through a native OS window handle that always
  wins Z-order/mouse-hit-testing over ordinary sibling widgets, which
  silently ate every click meant for `DrawOverlay` stacked on top of it.
  `_VideoSurface` instead paints each frame itself via
  `QMediaPlayer.setVideoSink(QVideoSink)` + `QVideoSink.videoFrameChanged`
  -> `QVideoFrame.toImage()`, the same frame-grab `thumbnail_loader.py`
  already used for its one-shot thumbnails, just applied continuously).
  `_VideoSurface` and an `overlay` (`DrawOverlay` in edit mode,
  `ReadOnlyCommentOverlay` in view mode — see `draw_overlay.py`) are
  stacked by `_VideoStack` — plain manual `setParent`/`show()`/
  `setGeometry`/`raise_()` on every resize, **not**
  `QStackedLayout(StackAll)`, which the root bug-history entry's "Second
  root cause" section covers: it left `DrawOverlay` with
  `isVisible() == False` despite correct geometry, confirmed via
  `plugins/studio/DebugConsole/`'s live debug log, and `_VideoStack` was
  the fix. `_VideoStack` also carries a third, always-visible layer,
  `_FrameNumberOverlay` — a HUD in the video's top-right corner showing
  the current frame number, raised topmost of the three but
  `WA_TransparentForMouseEvents` so it can never itself become a second
  thing standing between the mouse and `DrawOverlay` (the exact class of
  bug both that entry and the root
  `2026-07-20-text-tool-drew-strokes-simultaneously.md` were about).
  No visibility toggle for it (removed 2026-07-20 — "not necessary" per
  the user) — it's just always on in both modes now.
  `frame_number_overlay.set_frame_index` is called from
  `_on_position_changed` whenever the frame index actually changes.
  Text is bold, white, with a **black stroke drawn outside the fill**
  (`_STROKE_WIDTH`): the first version filled+stroked one `QPainterPath`,
  which centers the pen on the path outline so half the stroke width ate
  into the white fill from the edges inward, making the glyph look
  *thinner* instead of bolder — the opposite of what was asked. Fixed by
  stamping the black text at a 3x3 ring of pixel offsets first, then
  painting the white text once, dead center, on top — the black only ever
  shows through around the true glyph's outside edge, a standard cheap
  "poor man's outline" technique.

  `transport_row`'s button order is `prev_comment_button,
  prev_frame_button, play_button, next_frame_button, next_comment_button`
  (reordered 2026-07-20 per the user's own request — "previous comment,
  previous, play/stop, next, next comment"), followed by `goto_frame_spin`
  (a plain `QSpinBox`, added the same day for "ช่องกรอกเลข" — type a frame
  number and press Enter/lose focus to jump there via
  `_on_goto_frame_entered` -> `_jump_to_frame`; range kept in sync with the
  clip length from `_on_duration_changed`, value kept in sync with playback
  from `_on_position_changed`, both via `blockSignals` so neither echoes
  back as a fresh `editingFinished` jump). `play_button`'s icon swaps
  between `icons8-play-50.png`/`icons8-pause-50.png` (from `../images/` —
  see that folder's README) via `_set_paused_state` (`_PAUSE_ICON_PATH`,
  renamed from `_STOP_ICON_PATH` 2026-07-20 — a pause icon, not a stop
  icon, matches "play/stop" being an actual pause toggle rather than a
  hard stop), `prev_frame_button`/`next_frame_button`
  (`icons8-chevron-left-26.png`/`icons8-right-26.png`),
  `prev_comment_button`/`next_comment_button` (`icons8-double-left-26.png`/
  `icons8-double-right-26.png`, jump to the nearest frame with any saved
  comment via `_jump_to_comment_frame` — available in **both modes** since
  2026-07-20, were edit-mode-only before), `fps_label` (read-only "N FPS"
  info — replaced an editable `QSpinBox` 2026-07-20 per the user: "we're
  not going to change the frame rate value anyway"; `self._fps_value` is
  the actual source of truth `_fps()` returns now, no widget backing it),
  and a 0.01x-1.00x `speed_slider` -> `self.player.setPlaybackRate` (a
  slow-motion control, deliberately capped at normal speed rather than a
  general speed dial). `position_slider` moved into its own `slider_row`
  (`start_frame_label` "0" / the slider, stretched / `end_frame_label`,
  updated from `_on_duration_changed`'s `duration_ms` via the same fps
  math) — separated from `transport_row` 2026-07-20 per the user's own
  request. It's a `_CommentAwareSlider` (`QSlider` subclass), not a plain
  one: its `paintEvent` overlays small tick marks at every commented
  frame's position (`set_marks`, called from `_refresh_comment_indicators`)
  so scrubbing shows roughly where feedback exists along the timeline —
  approximate by design ("พออนุมานได้" — good enough to infer from, not
  pixel-perfect against the native groove rect for every Qt style). Frame
  indexing is `round(position_ms / 1000 * fps)` — `QMediaPlayer` has no
  native frame-accurate seek for arbitrary containers, so this is a
  deliberate approximation, confirmed acceptable with the user ("แบบโง่"
  — the whole feature is meant to stay simple).

  Keyboard shortcuts (all `QShortcut`, context
  `Qt.WidgetWithChildrenShortcut` so each only fires while this widget or
  a child has focus, all routed through `_is_typing()` —
  `QApplication.focusWidget()` isn't a `QLineEdit`/`QTextEdit`/
  `QPlainTextEdit` — so typing those same letters/space into
  `comment_thread.input_edit`, `goto_frame_spin`'s internal line edit, or a
  text box never hijacks the cursor): "A"/"D" step one frame
  back/forward, "Space" toggles play/pause, and "Shift+A"/"Shift+D" jump
  to the previous/next commented frame (`_jump_to_comment_frame_if_not_typing`
  — **both modes** since 2026-07-20, were edit-mode-only before) are all
  unconditional. Edit mode only: "Ctrl+Z"/"Ctrl+Shift+Z" mirror
  `undo_button`/`redo_button` -> `DrawOverlay.undo`/`redo` — the typing
  guard matters more here than most, since `QTextEdit`/`QPlainTextEdit`
  already have their own native Ctrl+Z, which must keep working normally
  while typing — and "1"/"2"/"3" select Brush/Eraser/Text
  (`_select_tool_if_not_typing` checks the corresponding toolbox button
  rather than calling `DrawOverlay.set_tool` directly, so the toolbox's
  own checked-state display stays in sync exactly like a mouse click
  would).

  `show_edit_tools` (constructor kwarg, default `True`) gates the
  interactive drawing machinery: when `True`, builds `DrawOverlay`
  (stacked over the video by `_VideoStack`) and a `tool_row` —
  `brush_tool_button`/`eraser_tool_button`/`text_tool_button`
  (`QToolButton`, all three checkable and mutually exclusive via one
  `QButtonGroup` — see `draw_overlay.py`'s `DrawOverlay._tool` for why
  Text became a real exclusive mode 2026-07-20, not a one-shot action,
  icons from `../images/icons8-{paint,eraser,text}-50.png` via
  `_set_button_icon`, which falls back to a text label when a given icon
  file isn't there yet either way; `core/theme.py`'s (app's top-level)
  `QToolButton:checked` rule is what actually makes the active tool
  visually obvious, filling it with the accent color) — each button's
  `toggled` connects straight to
  `DrawOverlay.set_tool(TOOL_BRUSH|TOOL_ERASER|TOOL_TEXT)` (only on
  `checked=True`, since the exclusive group also fires `toggled(False)`
  for whichever button just got deselected). `tool_row` is inserted as
  the *first* item in the main column — above `video_stack_widget`, in
  its own strip separate from `draw_row`'s other controls below the video
  — moved there 2026-07-20 per the user's own request, so which of the
  three tools is active reads at a glance rather than being mixed in
  among Color/Size/Clear/Undo/Redo. `draw_row` (still below the video)
  holds Color, a shared Size slider (`brush_slider`, drives both brush
  width and eraser radius — see `draw_overlay.py` — and stays in sync
  with the canvas's own "F" resize gesture via
  `DrawOverlay.toolSizeChanged` -> `_on_tool_size_changed`), Clear Frame,
  Undo (`icons8-undo-30.png`), Redo (`icons8-redo-30.png`).

  Since 2026-07-20, edit mode also builds a `CommentThread`
  (`comment_thread.py`, `self.comment_thread`) instead of the single
  `note_edit` `QTextEdit` it replaced: a Facebook-style multi-user comment
  thread ("เหมือนกด comment fb" — the user's own words), any number of
  comments per frame, each tagged with an author
  (`comment_store.current_username()`, `../core/comment_store.py`) and
  timestamp, each individually deletable. Unlike `draw_row`, `comment_thread`
  is *not* laid out inside `main_column` — it lives in `right_column` (see
  "Right-hand column" below), moved there the same day per the user's own
  request ("ย้ายช่อง comment ไปทางขวามือ") so the whole right edge of the
  widget is comment-related. `commentsChanged` -> `_on_comments_changed`
  -> `_save_current_frame(comments=...)`, owning loading/saving each
  frame's strokes + comments + text boxes through `../core/comment_store.py`.
  A frame saved before 2026-07-20 may still only have the old single
  `"note"` string — `_migrate_comments` (a `@staticmethod` on
  `PlayerWidget`, called from `_load_current_frame`) wraps that into a
  one-item comments list for display; saving the thread again (any
  post/delete) replaces `"note"` with `"comments"` for that frame entirely.

  When `show_edit_tools=False` (the library page's inline preview), none
  of that interactive toolbar/canvas machinery is built — but
  `load_video` still calls `comment_store.load` either way (changed
  2026-07-20; used to be `show_edit_tools`-gated) since `comment_sidebar`
  needs to know which frames have comments in both modes, and view mode
  instead builds a `ReadOnlyCommentOverlay` (see `draw_overlay.py`) — a
  read-only rendering of each frame's saved strokes/text boxes, stacked
  in place of `DrawOverlay` — plus, view-mode-only, two more widgets added
  at the end of `transport_row`: `toggle_comment_overlay_button` (icon-only,
  checkable, default checked — swaps between `icons8-hide-50.png` (checked,
  i.e. comments are currently shown — click to hide) and
  `icons8-show-50.png` (unchecked) via `_update_comment_overlay_toggle_icon`,
  called from both `__init__` and `_on_toggle_comment_overlay`; was a plain
  "Show Comments" text button before 2026-07-20) ->
  `readonly_comment_overlay.setVisible`, so the plain viewing page can see
  comment content without opening the full Edit Video dialog; and
  `edit_comment_button` (`icons8-edit-50.png`, fixed
  `_EDIT_COMMENT_BUTTON_SIZE`x`_EDIT_COMMENT_BUTTON_SIZE` = 32x32 square —
  "ปุ่มสี่เหลี่ยม 1:1", moved here from `video_library_page.py` 2026-07-20 so
  it sits directly beside Show/Hide Comments instead of in its own row
  below the whole player — disabled until `load_video` is called, emits
  `editCommentRequested` for the host page to actually open
  `EditVideoDialog`). `_load_current_frame`
  branches on `show_edit_tools` to feed either `DrawOverlay.load_frame`
  or `ReadOnlyCommentOverlay.set_frame` from the same
  `self._frames["frames"]` entry.

  **Right-hand column** (`right_column`, a plain `QWidget`) holds
  `comment_sidebar` (a `CommentSidebar` — see `comment_sidebar.py`) on
  top, `stretch=1` since its own height should fill whatever
  `comment_thread` (edit mode only, underneath it, not stretched — its
  `thread_scroll` already caps its own height, see `comment_thread.py`)
  doesn't use. `comment_sidebar` is built unconditionally, in both modes,
  per the user's own 2026-07-20 request that view mode get "the same"
  sidebar edit mode has; `comment_thread` only exists in edit mode (see
  its own entry above) and is only added to `right_column` when
  `show_edit_tools` is `True` — moved here from underneath `draw_row` the
  same day per the user's own request ("ย้ายช่อง comment ไปทางขวามือ").
  `self` is an outer `QHBoxLayout` with everything else wrapped in a
  `main_column` widget instead (`main_column, stretch=1` + `right_column`)
  so the whole right-hand column sits to the right of the whole player,
  not just the video. `comment_sidebar.frameSelected` -> `_jump_to_frame`
  (jumps to an exact frame, unlike `_jump_to_comment_frame`'s "nearest"
  search) is connected once in `__init__`; `_refresh_comment_indicators()`
  (rebuilds `comment_sidebar`'s rows *and* `position_slider`'s tick marks
  from `self._frames["frames"]`) is called from `load_video`,
  `clear_video`, and the end of `_save_current_frame` — i.e. whenever the
  underlying comment data actually changes, not on every frame navigation.
  `_on_position_changed` calls `comment_sidebar.set_current_frame(...)`
  (highlights the matching row, if any) alongside
  `frame_number_overlay.set_frame_index(...)` whenever the frame index
  changes. `_set_button_icon` (renamed from `_set_tool_icon` 2026-07-20,
  since it's no longer toolbox-specific) is a `@staticmethod` — used
  throughout this file for every icon button, edit and view mode alike.
- `comment_sidebar.py` — `CommentSidebar`, added 2026-07-20, rewritten the
  same day to match `interface/settings/settings_view.py`'s (the app's
  top-level `interface/`) `SettingsView.tab_list` style per the user's own
  request ("ให้ใช้เป็น tab แบบเดียวกับใน setting") instead of the card grid
  it started as: a plain fixed-width (`_WIDTH`) `QListWidget`, one row per
  frame with a saved comment, sorted top-to-bottom by frame index, each
  row just the frame number (no "Frame" label — "คำว่า frame ไม่ต้องเอามา",
  the user's own words). `set_frames(frames_dict)` rebuilds every row from
  scratch from `PlayerWidget._frames["frames"]`. Deliberately connects to
  `currentRowChanged`, not `itemClicked` — `QListWidget`'s native
  press-and-drag-across-rows selection behavior (the same thing
  `SettingsView.tab_list` gets for free) then scrubs through commented
  frames live as you drag, matching the user's own "ลากเลือกได้" (can be
  drag-selected) request. `set_current_frame(index)` highlights whichever
  row matches the frame currently playing without emitting
  `frameSelected` (`_suppress_selection_signal` guards against
  `PlayerWidget`'s own state echoing back in as a fresh jump request).
- `draw_overlay.py` — `DrawOverlay`/`Stroke`/`_TextBoxItem`/`_DragHandle`:
  the transparent freehand canvas. Fixed-shape pen only (color + width), a
  whole-stroke eraser (removes any stroke with a point near the cursor,
  not pixel-level), and an in-memory (not persisted) snapshot-based
  undo/redo stack pair scoped to the current frame only — resets whenever
  a different frame is loaded. `undo()` pushes the pre-undo state onto
  `_redo_stack` before popping `_undo_stack` (and vice versa for
  `redo()`); `_push_undo()` (called before any new stroke or
  `clear_frame()`) clears `_redo_stack`, the standard "a new edit
  invalidates redo history" rule — added 2026-07-20 alongside a Redo
  button next to Undo and "Ctrl+Z"/"Ctrl+Shift+Z" shortcuts (see
  `player_widget.py`). Text boxes are not part of this stack, matching
  undo's original strokes-only scope. `_tool` (one of module-level
  `TOOL_BRUSH`/`TOOL_ERASER`/`TOOL_TEXT`, set via `set_tool`) is the single
  source of truth every mouse handler branches on — fixed 2026-07-20 after
  a real "repositioning a text box also draws a stroke at the same time"
  report (see `../bug-history/README.md`'s pointer to the root entry):
  Text used to be a one-shot `add_text_box()` action that left Brush's
  drawing active underneath it the whole time, instead of a true exclusive
  mode. With `_tool == TOOL_TEXT`, `mousePressEvent` places a new
  `_TextBoxItem` at the click position instead of starting a stroke, and
  `mouseMoveEvent`/`mouseReleaseEvent` both skip the brush/eraser path
  entirely — see `player_widget.py`'s toolbox for how the three
  `QToolButton`s stay mutually exclusive and each call `set_tool`.
  `_brush_width` is one shared "tool size" (pixels) for *both* the
  brush's stroke width and the eraser's hit-test radius (`_erase_near`
  converts it to normalized widget-space at call time via
  `self._brush_width / self.width()`) — the toolbar's Size slider and the
  canvas's own "F" resize gesture (below, disabled while `_tool ==
  TOOL_TEXT` since size doesn't apply to placing a text box) both just
  adjust this one value, whichever of brush/eraser happens to be active.
  `setMouseTracking(True)` + a hollow circle painted at the cursor
  position (`_paint_hover_indicator`, radius = `_brush_width / 2` for the
  brush or `_brush_width` for the eraser; hidden while drawing is disabled
  or the cursor leaves the widget) previews the exact brush/eraser size
  before a stroke is even started.
  **"F" resize gesture**: `StrongFocus` + `enterEvent` grabbing focus on
  hover (so it works without an explicit click first, like a 3D
  viewport), `keyPressEvent` handling `F` (start, or confirm if already
  resizing) and `Escape` (cancel, reverting to the pre-gesture size) —
  while active, `mouseMoveEvent` maps horizontal mouse delta to size
  (`_RESIZE_PIXELS_PER_UNIT` px per unit, clamped `_MIN_TOOL_SIZE`-
  `_MAX_TOOL_SIZE`) instead of drawing/erasing, and a left click also
  confirms (`mousePressEvent`/`mouseReleaseEvent` both short-circuit while
  `_resizing`). Emits `toolSizeChanged` only from this gesture (not from
  `set_brush_width`, which would just echo the slider) so
  `player_widget.py`'s Size slider can mirror a size change made this way.
  `setAttribute(Qt.WA_AlwaysStackOnTop)` on the overlay was the first
  (insufficient on its own) attempt at fixing the "brush doesn't paint,
  dragging does nothing" bug — the real fix was replacing `QVideoWidget`
  with `player_widget.py`'s `_VideoSurface`, see that bullet and the root
  `bug-history/2026-07-20-draw-overlay-native-video-widget.md`; the
  attribute was left on as a harmless, no-longer-load-bearing leftover.
  `mousePressEvent`/`mouseMoveEvent`/`resizeEvent`/the hover-indicator's
  early-return path all call
  `core.extensibility.debug_log.log("UkoreShot.Draw", ...)` (the app's
  top-level `core/`, module-level `debug_log.register_source(_DEBUG_SOURCE)`
  at import time) — added 2026-07-20 alongside `plugins/studio/DebugConsole/`
  so this feature's mouse-event/paint behavior can be inspected live in-app
  (this app is normally launched via `pythonw.exe`, no console at all) —
  see that plugin's own README for the general mechanism. Kept as
  permanent light instrumentation, not temporary debug prints.
  `_TextBoxItem` (`QFrame`, object name `textBoxItem`, styled via the
  app's top-level `core/theme.py`) is a draggable, editable text
  annotation — as many as wanted, one per click on the canvas while the
  Text tool is selected (`mousePressEvent`'s `_tool == TOOL_TEXT` branch,
  placed exactly at the click position; before 2026-07-20 this was a
  toolbar button that always added at a cascading default position
  instead). Dragging only works from the `_DragHandle` ("⋮⋮") strip, never
  the text field itself, so placing a cursor to type never fights with
  moving the box. Both strokes and text boxes are keyed to the exact
  frame index currently loaded (`load_frame(strokes, text_boxes)`) so
  scrubbing between frames doesn't smear one frame's annotations onto
  another; position is normalized (0-1, top-left corner) the same way
  `Stroke.points` already is, so boxes track correctly across resizes
  (`DrawOverlay.resizeEvent`). Module-level
  `paint_stroke_points(painter, points, color, width, w, h)` is
  `DrawOverlay._paint_points`'s exact math factored out (added 2026-07-20)
  so `ReadOnlyCommentOverlay` (same file) can paint a stroke
  pixel-identically without depending on `DrawOverlay` or duplicating the
  path-building logic. `ReadOnlyCommentOverlay` — view-mode-only, no mouse
  handling at all (`WA_TransparentForMouseEvents`, same reasoning as
  `_FrameNumberOverlay`), just `set_frame(strokes, text_boxes)` ->
  `paintEvent` re-painting strokes via `paint_stroke_points` and text
  boxes as plain rounded rectangles with the note text drawn inside (no
  drag handle, no delete button, no editable field — this is display-only).
  `player_widget.py` stacks it in `DrawOverlay`'s place inside
  `_VideoStack` when `show_edit_tools=False`, toggled by that plugin's own
  `toggle_comment_overlay_button`.
- `edit_video_dialog.py` — `EditVideoDialog` (`QDialog`), opened by
  `PlayerWidget`'s own `editCommentRequested` signal (view mode's
  `edit_comment_button`, connected by `video_library_page.py`): just embeds
  one `PlayerWidget(show_edit_tools=True)` loaded with the selected video,
  so the drawing/comment tools only appear when an artist deliberately
  opens it instead of always being visible while just watching.
- `comment_thread.py` — `CommentThread` + `_CommentBubble`, added
  2026-07-20: the Facebook-style multi-user comment thread embedded by
  edit-mode `PlayerWidget` (`self.comment_thread`), replacing the old
  single `note_edit` `QTextEdit`. `set_comments`/`current_comments` are its
  external interface; `commentsChanged` fires after any post or delete.
  Internally just a scrollable `QVBoxLayout` of `_CommentBubble` rows
  (`QFrame`, object name `commentBubble`, styled via the app's top-level
  `core/theme.py`) — each showing author + timestamp + text + a small "×"
  delete button (`deleteRequested`, no per-comment ownership/permission
  check — the whole ask was "มีปุ่มลบ comment", not "only your own can be
  deleted") — plus a `QLineEdit` + Post button pinned below the scroll
  area for adding a new one. New comments are tagged via
  `../core/comment_store.py`'s `current_username()`.

**Working here:** stay inside `interface/` unless the change needs a new
top-level `core/` primitive (the app's own, a genuinely different package
— see the naming note above) or a `../core/` addition this UI depends on.
The `_VideoCard`/`_TextBoxItem`/`_CommentBubble` QSS rules
(`QFrame#videoCard`, `QFrame#textBoxItem`, `QFrame#commentBubble` +
friends) were added to the app's top-level `core/theme.py`'s shared
stylesheet rather than a local `setStyleSheet` — that's the "needs a new
`core/` primitive" exception, matching the existing `QFrame#repoCard`
rules `interface/login/repo_picker.py` already relies on.
