# plugins/studio/UkoreShot/

Per-repo playblast video library + review. A normal (non-persistent)
`SectionSpec` sidebar tab — visible only for repos where it's checked under
Settings > Repo > Enable Plugin (`Repo.active_plugin_ids`), the same
mechanism every other plugin's sidebar tab already uses (see
`interface/main_window.py`'s `_apply_plugin_visibility`) — no add-on-style
gating needed. Companion to `plugins/studio/UkoreShotPlayblast/`, which
writes the video files this plugin's library lists.

## Where the video library folder comes from

Confirmed with the user: UkoreShot does **not** own its own free-text
folder setting. Instead, Repository Setting > UkoreShot
(`repo_video_settings_page.py`) lets a studio admin pick one of the active
repo's own already-declared **Custom Paths** (Repository Setting >
Custom Paths > Create Input Path, owned by `plugins/studio/project_editor/`
— see that plugin's README) as this repo's playblast video root. Read
directly off `project_editor`'s shared `PluginConfigStore`
(`data/plugins/studio/project_editor.json`), the "convention, not import"
pattern every cross-plugin read in this app uses — see
`plugins/README.md`'s "Sharing data with another plugin". Auto-uses the
repo's only declared Custom Path if there's exactly one (no explicit choice
needed); requires an explicit pick if there's more than one; resolves to
nothing if there are none yet. See `video_path_store.py`'s
`resolve_video_root` for the exact resolution order (mirrors
`PublishApi.repo_paths.get_publish_root`'s own convention).

`UkoreShotPlayblast`'s Maya-side `function.py` reads UkoreShot's own choice
the same "construct the store straight off disk" way (no shared bridge file
needed) — see that plugin's README.

## Files

- `manifest.json` — plugin id `ukore_shot`.
- `plugin.py` — `register(api)`: registers the sidebar section (order 50)
  and the `CATEGORY_REPO` "UkoreShot" settings tab (order 125).
- `video_path_store.py` — reads the active repo's Custom Paths off
  `project_editor`'s store, stores UkoreShot's own chosen `custom_path_id`
  in its own `PluginConfigStore` (`data/plugins/studio/ukore_shot.json`,
  `repo_video_custom_path: {"<project_id>:<repo_id>": "<custom_path_id>"}`),
  and `resolve_video_root(api, project_id, repo_id)` — joins
  `workspace_root / repo.local_path / custom_path.path` into the actual
  absolute folder.
- `repo_video_settings_page.py` — `RepoVideoSettingsPage`, the
  `CATEGORY_REPO` Settings tab. Same self-resolving-active-repo `refresh()`
  + "list of choices, auto-use if there's only one" pattern as
  `plugins/studio/RigPublisher/settings_page.py`'s
  `RigPublisherSettingsPage`, just pointed at `custom_paths` instead of
  `pipeline_inputs`.
- `video_library_page.py` — `UkoreShotPage`, the section's top-level
  widget. A thumbnail-grid `QListWidget` (left, `IconMode`, best-effort
  thumbnails via `thumbnail_loader.py`) of `.mov`/`.mp4`/`.avi` files under
  `resolve_video_root(...)`, sorted by mtime desc, plus `PlayerWidget`
  (right) for whichever one is selected. Implements the standard
  `set_repo(project, repo, workspace_root)` page protocol
  (`interface/main_window.py`'s `_apply_to_current_page`).
- `thumbnail_loader.py` — `ThumbnailLoader`: one hidden `QMediaPlayer` +
  `QVideoSink` pair, processed one video at a time, grabs the first
  decodable frame as a `QPixmap` for the list icon. Best-effort — a video
  it can't decode a frame from just shows with no icon, nothing crashes.
- `player_widget.py` — `PlayerWidget`: `QMediaPlayer` + `QVideoWidget` +
  `DrawOverlay` stacked together via a `QStackedLayout` (`StackAll` mode),
  transport controls (play/pause, prev/next-frame, scrub slider, an FPS
  spin box), a draw toolbar (color, brush size, eraser, clear frame, undo),
  and a per-frame text comment box. Frame indexing is
  `round(position_ms / 1000 * fps)` — `QMediaPlayer` has no native
  frame-accurate seek for arbitrary containers, so this is a deliberate
  FPS-based approximation, confirmed acceptable with the user
  ("แบบโง่" — the whole feature is meant to stay simple). Owns loading/
  saving each frame's strokes + note through `comment_store.py`.
- `draw_overlay.py` — `DrawOverlay`/`Stroke`: the transparent freehand
  canvas. Fixed-shape pen only (color + width), a whole-stroke eraser
  (removes any stroke with a point near the cursor, not pixel-level), and
  an in-memory (not persisted) snapshot-based undo stack scoped to the
  current frame only — resets whenever a different frame is loaded.
- `comment_store.py` — sidecar JSON persistence, one file per video:
  `<video_path>.ukoreshot.json` next to the video itself (travels with the
  shared library folder, no separate app data store). Shape:
  `{"frames": {"<frame_index>": {"strokes": [{"color", "width", "points"}], "note": "..."}}}`,
  points stored normalized 0-1 in widget space.

**Working here:** stay inside this folder unless the change needs a new
`core/` primitive, or touches `plugins/studio/project_editor/`'s Custom
Paths data shape (read-only, via the convention above) or
`plugins/studio/UkoreShotPlayblast/`'s output (read-only, both plugins just
happen to agree on the same resolved folder — see that plugin's own
README for the Maya-side half of this feature).
