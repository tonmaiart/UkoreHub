# data/

Runtime data UkoreHub's `core/` stores read and write — not code. See
`core/README.md` (`store.py`, `program_store.py`) and
`core/extensibility/README.md` (`config_store.py`) for the classes that own
these files; this README is just what's on disk and whether it's shared.

**Working here:** don't open these files unless the task specifically needs
their current contents (e.g. debugging a stale value, checking a real id).
Never open an image file in here to "look at it" — there's nothing textual
to read, and it wastes context for zero benefit. Never confuse this with
`projects/` at the repo root, which is the actual gitignored workspace root
(real cloned repos) — see root `CLAUDE.md`; that one is never read at all
unless explicitly asked.

## JSON stores

- `projects.json` — `MetadataStore`, the Project/Repo registry.
  **Shared/git-tracked.** Can grow large as repos/thumbnails accumulate —
  prefer `programs.json`/`system_config.json` below if you just need "an
  example of the shape."
- `programs.json` — `ProgramStore`, the shared software catalog. Shared/
  git-tracked, small.
- `system_config.json` — `SystemConfigStore`, studio-wide settings (GitHub
  OAuth client id). Shared/git-tracked, tiny.
- `projects.example.json` — a checked-in sample shape for `projects.json`,
  not read by the app itself.
- `plugins/core/*.json` — `PluginConfigStore` files, one per `plugin_id` a
  plugin's `register(api)` chose with `shared=True`
  (`api.plugin_config_store(plugin_id, shared=True)`). Shared/git-tracked.
  Named after `shared=True/False`, not after which `plugins/` source root
  the calling plugin itself lives under — a `plugins/repo_internal/` or
  `cache/plugins/` plugin still writes here for `shared=True`. The
  `shared=False` counterpart (per-machine) writes to
  `cache/plugin_local_config/*.json` instead — see `cache/README.md`.

Everything per-machine/gitignored that used to live here
(`local_config.json`, `github_token.json`, `webengine_profile/`,
`plugins/local/*.json`) now lives under `cache/` instead — see
`cache/README.md`. This means `data/` today holds only files meant to be
the same for everyone at the studio.

## Binary/image directories — not code, skip unless verifying a specific file

- `thumbnails/` — per-repo thumbnail images, filename = `Repo.
  thumbnail_filename`.
- `program_icons/` — per-`Program` icons, filename = `Program.
  icon_filename`.
- `browser_link_icons/` — per-`BrowserLink` icon overrides, filename =
  `BrowserLink.icon_filename`. Falls back to `icons/icons8-browser-50.png`
  when unset.
- `icons/` — static app-chrome icons (Setting gear, Sidebar's
  SectionTabList's About/Browser/Explorer/Submit icons), not tied to any
  JSON store record — just fixed asset files referenced directly by path
  from `interface/`.

All are referenced by filename from the JSON stores above (except `icons/`,
referenced directly by path); if a task needs to confirm a file exists,
check with a directory listing, not by opening the image.
