# plugins/studio/UkoreShot/

Per-repo playblast video library + review. A normal (non-persistent)
`SectionSpec` sidebar tab — visible only for repos where it's checked under
Settings > Repo > Enable Plugin (`Repo.active_plugin_ids`), the same
mechanism every other plugin's sidebar tab already uses (see
`interface/main_window.py`'s `_apply_plugin_visibility`) — no add-on-style
gating needed. Companion to `plugins/studio/UkorePlayblast/`, which
writes the video files this plugin's library lists.

## Structure

Split into subfolders by concern on 2026-07-21, specifically so a session
can **read only the subfolder(s) a given task actually touches** instead
of the whole plugin — this folder had grown to over a dozen flat files,
most of them irrelevant to any one task:

- [`core/`](core/README.md) — non-UI logic: video-root path resolution,
  comment persistence, playblast filename parsing. No PySide6 imports.
- [`interface/`](interface/README.md) — every PySide6 widget/page/dialog
  this plugin has.
- [`images/`](images/README.md) — this plugin's own icon files (not the
  shared `data/icons/` every other plugin uses — see that README for why).
- [`bug-history/`](bug-history/README.md) — bugs fixed specifically within
  this plugin's own code, same format as the repo-root `bug-history/`,
  going forward from 2026-07-21.
- `manifest.json` / `plugin.py` / `__init__.py` — plugin entry point,
  stay at this top level: the plugin loader
  (`core/extensibility/loader.py`'s `_load_one`) looks for both
  `manifest.json` and `manifest.json`'s `entry_point` directly inside a
  plugin's own top-level directory, not in a subfolder, and only ever
  imports `plugin.py` itself that way — everything `plugin.py` imports
  from `interface/`/`core/` is a normal absolute Python import, so those
  subfolders are otherwise free to be organized however makes sense.

**Before touching a file in one of the four subfolders above, read that
subfolder's own README first** — the same "read the local README before
opening individual files" rule root `CLAUDE.md` already applies to every
top-level folder in this repo, just one level deeper here. Concretely: a
task about where videos are found on disk or how comments persist only
needs `core/`; a task about a button, dialog, or layout only needs
`interface/`; don't open a sibling subfolder "just in case" unless the
task genuinely crosses the boundary (same discipline the `ukorehub-plugin`
skill already asks for between *different* plugins — this applies it one
level down, *within* this one plugin).

**Naming collision to know about:** two different files in this plugin
import a bare `from core...` — `core/comment_store.py`'s
`from core.store import LocalConfigStore` and
`interface/draw_overlay.py`'s `from core.extensibility import debug_log`.
Both mean the app's own **top-level** `core/` package
(`C:\Tonmai\UkoreHub\core\`), never this plugin's own `core/` subfolder —
they're absolute imports, resolved from the repo root regardless of where
the importing file lives, so there's no actual ambiguity at runtime; it's
only confusing to a human skimming the two folders side by side. See
`core/README.md`'s own naming note for more.

For the `ukoreshot` skill (project-scoped, for working specifically in
this plugin), see `.claude/skills/ukoreshot/SKILL.md`.

## Where the video library folder comes from

UkoreShot does **not** own its own free-text folder setting — a studio
admin picks one of the active repo's own declared Custom Paths under
Repository Setting > UkoreShot instead. See `core/README.md`'s
`video_path_store.py` entry for the exact resolution order and how it
ties into `plugins/studio/project_editor/`'s Custom Paths and
`plugins/studio/UkorePlayblast/`'s output folder.

**Working here:** stay inside this plugin folder (respecting the
subfolder-scoping rule above) unless the change needs a new top-level
`core/` primitive, or touches `plugins/studio/project_editor/`'s Custom
Paths data shape (read-only, via the convention in `core/README.md`) or
`plugins/studio/UkorePlayblast/`'s output (read-only, both plugins just
happen to agree on the same resolved folder — see that plugin's own
README for the Maya-side half of this feature).
