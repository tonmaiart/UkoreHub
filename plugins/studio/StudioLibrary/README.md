# plugins/studio/StudioLibrary/

Vendored copy of [Studio Library](https://github.com/krathjen/studiolibrary)
for Maya (pose/animation library) — relocated here on 2026-07-13 from where
it had been parked at `add-on/UnrealLauncher/dev/studiolibrary-2.21.1/`
(unrelated to Unreal; that was just a scratch location). Self-contained —
no dependency on MayaToolkit's `tmlib`/`UkoreMaya`.

Was its own `add-on/StudioLibrary/`, folded into
`plugins/studio/maya_launcher/StudioLibrary/` as one of 7 nested tools
during the 2026-07-14 consolidation, then split back out to this top-level
plugin on 2026-07-19 — see `plugins/studio/maya_launcher/README.md` for why.

- `manifest.json` / `plugin.py` — standard plugin registration (see
  `plugins/README.md`). `plugin.py` only contributes `maya-scripts/` to
  `plugins/studio/maya_launcher/`'s shared `maya_launcher_env_bridge`
  `PluginConfigStore` PYTHONPATH bridge (same convention as
  `plugins/studio/DreamwallPicker/plugin.py`) — no file opener, no UI of
  its own inside UkoreHub. No direct import relationship with
  `maya_launcher` — just the shared `PluginConfigStore` id convention.
- `maya-scripts/` — the five vendored packages, flat (matches upstream's own
  `src/` layout): `studiolibrary`, `studiolibrarymaya`, `mutils`,
  `studioqt`, `studiovendor`.
- `vendor/` — upstream's own docs/license/installer, kept for attribution
  (`LICENSE.md`, `DOCS.md`, `README.md`, `install.py`/`.mel`/`.gif`/`.txt`,
  `config/readme.md`). Not on `PYTHONPATH` — nothing here is imported at
  runtime.

## Entry point

`plugins/studio/MayaToolkit/maya-scripts/UkoreMaya/core/function.py`'s
`studio_library()` is the caller (wired into the UkoreMenu). It used to
hardcode an absolute path (`G:\My Drive\Mellowstar\dev\studiolibrary-2.21.1\src`)
with a manual `sys.path.insert` and a stale, unrelated existence check —
that's gone now that this plugin's `plugin.py` puts `maya-scripts/` on
`PYTHONPATH` itself; the function is just `import studiolibrary;
studiolibrary.main()`.

## Working on this plugin

Read/edit only files under this folder — see `plugins/README.md`'s
plugin-scoping note (and the `ukorehub-plugin` skill). This is third-party
vendored code: prefer not to modify the package internals directly unless
there's a specific reason (upstream: https://github.com/krathjen/studiolibrary).
