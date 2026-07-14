# add-on/StudioLibrary/

Vendored copy of [Studio Library](https://github.com/krathjen/studiolibrary)
for Maya (pose/animation library) — relocated here on 2026-07-13 from where
it had been parked at `add-on/UnrealLauncher/dev/studiolibrary-2.21.1/`
(unrelated to Unreal; that was just a scratch location). Self-contained —
no dependency on MayaToolkit's `tmlib`/`UkoreMaya`.

- `manifest.json` / `plugin.py` — standard add-on registration (see
  `add-on/README.md`). `plugin.py` only contributes `maya-scripts/` to the
  shared `maya_launcher_env_bridge` PYTHONPATH bridge (same convention as
  `add-on/DreamwallPicker/plugin.py`) — no file opener or repo-addon panel.
- `maya-scripts/` — the five vendored packages, flat (matches upstream's own
  `src/` layout): `studiolibrary`, `studiolibrarymaya`, `mutils`,
  `studioqt`, `studiovendor`.
- `vendor/` — upstream's own docs/license/installer, kept for attribution
  (`LICENSE.md`, `DOCS.md`, `README.md`, `install.py`/`.mel`/`.gif`/`.txt`,
  `config/readme.md`). Not on `PYTHONPATH` — nothing here is imported at
  runtime.

## Entry point

`add-on/MayaToolkit/maya-scripts/UkoreMaya/core/function.py`'s
`studio_library()` is the caller (wired into the UkoreMenu). It used to
hardcode an absolute path (`G:\My Drive\Mellowstar\dev\studiolibrary-2.21.1\src`)
with a manual `sys.path.insert` and a stale, unrelated existence check —
that's gone now that this add-on's `plugin.py` puts `maya-scripts/` on
`PYTHONPATH` itself; the function is just `import studiolibrary;
studiolibrary.main()`.

## Working on this add-on

Read/edit only files under this folder — see `add-on/README.md`'s
add-on-scoping note (and the `ukorehub-addon` skill). This is third-party
vendored code: prefer not to modify the package internals directly unless
there's a specific reason (upstream: https://github.com/krathjen/studiolibrary).
