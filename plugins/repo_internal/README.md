# plugins/repo_internal/

Bundled with the app exactly like `plugins/core/` — git-tracked, shipped
via `self_update.py`'s whole-tree `git pull`, no separate fetch — but
gated **opt-in** per repo instead of `core/`'s always-on. A plugin here
stays hidden for every repo until that repo explicitly requires it
(`Repo.required_plugin_ids`, set from Settings > Repo > Requirements &
Plugins, `interface/repo_settings/requirements_and_plugins_page.py`'s
"Internal Plugin" list), the same "off until required" shape as a
Program requirement (`core/models.py`'s `Project.programs`). See `plugins/README.md` for
how this compares to `plugins/core/` and `cache/plugins/`, and
`core/extensibility/README.md` for the discovery mechanics
(`core/extensibility/loader.py`'s `plugin_source()` returns
`"repo_internal"` for anything discovered here).

Use this folder instead of `plugins/core/` for a plugin that only some
repos actually need — `plugins/core/` is always visible for every repo
with no per-repo opt-out at all, which is the wrong default for something
niche; adding it here instead keeps every existing repo unaffected until a
repo owner opts in.

Same authoring shape as any other plugin (`manifest.json` + `plugin.py`
with `register(api)`, optionally a real Python package for a multi-file
plugin — see `plugins/README.md`'s "Minimum folder shape" and "Multi-file
plugins" sections). As of 2026-08-04, home to eight Maya-pipeline plugins
moved here from `plugins/core/` (none of them need to be on for every
repo — a non-Maya project shouldn't see a Maya Launcher tab):
`MayaNgskin`, `MayaPublisher`, `MayaToolkit`, `PublishApi`,
`UkorePlayblast`, `UkoreReferenceEditor`, and `maya_launcher` itself.
`MayaPublisher` merged the former `RigPublisher`/`ModelPublisher`/
`AnimationPublisher` (2026-08-05) — see its own README. `UkoreShot` and
`MayaNgskin` were two of these eight too, until each moved again — out of
this repo entirely, into their own standalone git repositories cloned at
`cache/plugins/UkoreShot/` (2026-08-08) and `cache/plugins/MayaNgSkin/`
(2026-08-08) respectively (see `plugins/README.md`'s `cache/plugins/`
section) — `UkorePlayblast` (UkoreShot's companion) stayed here, as did
`maya_launcher` itself, still read by every remaining/moved-out tool via
the shared `maya_launcher_env_bridge` convention.
