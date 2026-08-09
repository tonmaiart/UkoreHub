# assets/

Git-tracked binary images UkoreHub ships or accumulates — never cloud-synced
and never written by `core/cloud_sync.py`, unlike everything in `data/` (see
`data/README.md`). Split out from `data/` on 2026-08-09 specifically because
these files aren't part of that sync system at all, and living alongside it
made "is this file cloud-synced?" a per-file question instead of a per-folder
one.

**Working here:** don't open these files unless the task specifically needs
to verify one exists — there's nothing textual to read. Use a directory
listing, not an image viewer.

- `thumbnails/` — per-repo thumbnail images, filename = `Repo.
  thumbnail_filename` (`core/models.py`). Resolved via
  `MetadataStore.resolve_thumbnail_path`/`thumbnails_dir`
  (`core/store.py`).
- `program_icons/` — per-`Program` icons, filename = `Program.
  icon_filename` (`core/models.py`, part of a Project's own `programs`
  list). Resolved via `MetadataStore.resolve_program_icon_path`/
  `program_icons_dir` (`core/store.py`).
- `browser_link_icons/` — per-`BrowserLink` icon overrides, filename =
  `BrowserLink.icon_filename`. Falls back to `icons/icons8-browser-50.png`
  when unset. Resolved via
  `MetadataStore.resolve_browser_link_icon_path`/`browser_link_icons_dir`.
- `icons/` — static app-chrome icons (Setting gear, Sidebar's
  SectionTabList's About/Browser/Explorer/Submit icons), not tied to any
  JSON store record — fixed asset files referenced directly by path
  (`api.app_root / "assets" / "icons"`) from `interface/` and each
  `plugins/core/*/plugin.py` that registers a sidebar section.

`thumbnails/`, `program_icons/`, and `browser_link_icons/` are referenced by
filename from the JSON stores in `data/`; `icons/` is referenced directly by
path since it has no owning store. `MetadataStore` takes an `assets_dir`
constructor param (defaulting to `<repo_root>/assets` when omitted) rather
than deriving it from `json_path`'s own folder — that's what lets `data/`'s
JSON files move to a cloud-synced cache without dragging these image
folders along with them.
