# plugins/studio/DebugConsole/

A live viewer for `core/extensibility/debug_log.py`'s in-memory debug log
bus — any plugin (or `core/` module) can call
`core.extensibility.debug_log.log(source, message)` from anywhere at
runtime and see it show up here immediately, without needing a console
window (this app is normally launched via `pythonw.exe`, no console at
all — see `bug-history/2026-07-20-draw-overlay-native-video-widget.md`'s
own debugging session for why that mattered). Added 2026-07-20 to debug
`plugins/studio/UkoreShot/`'s "brush doesn't paint" investigation; kept as
a general-purpose tool since the underlying bus is generic, not
UkoreShot-specific.

`manifest.json`'s `"core": true` makes this section always visible
regardless of any repo's `active_plugin_ids` (see
`core/extensibility/README.md`'s `loader.py` bullet) — a debug console is
orthogonal to which repo is active, so gating it per-repo like an
artist-facing tool would just mean re-enabling it for every existing and
future repo for no benefit.

## Files

- `manifest.json` — plugin id `debug_console`, `"core": true`.
- `plugin.py` — `register(api)`: builds one `DebugConsolePage` and
  registers it as a section (order 900, near the bottom of the sidebar —
  this is a developer tool, not meant to be prominent).
- `debug_console_page.py` — `DebugConsolePage`: a source filter
  (`QComboBox`, "All sources" + every name `debug_log.sources()` knows
  about, rebuilt whenever a new source appears) above a read-only,
  monospace `QPlainTextEdit` log view, plus a "Clear" button
  (`debug_log.clear()`). Subscribes once via `debug_log.add_listener` in
  `__init__` and never unsubscribes — this page is built once in
  `plugin.py`'s `register(api)` and lives for the app's whole lifetime,
  same as every other plugin's `page_factory`-returned instance, so
  there's no natural teardown point to unsubscribe at.

## Using this from another plugin

```python
from core.extensibility import debug_log

debug_log.register_source("YourPlugin.SomeFeature")  # optional — log() auto-registers too

debug_log.log("YourPlugin.SomeFeature", "something happened")
```

No `api` handle needed — this is a direct-import module, same
"construct/reach directly, convention not import" pattern
`core/extensibility/config_store.py`'s `PluginConfigStore` already uses
elsewhere in this codebase (see `plugins/README.md`'s "Sharing data with
another plugin"), just for log messages instead of persisted JSON. Safe
to call from deep runtime code (a widget's `mousePressEvent`, a Maya-side
script, etc.), not just inside `register(api)`. Not persisted — cleared on
app restart or via the "Clear" button — and capped at 1000 entries; this
is a live troubleshooting aid, not an audit log.

**Working here:** this plugin has zero UkoreShot-specific code — it only
reads the generic `debug_log` bus. `plugins/studio/UkoreShot/draw_overlay.py`
is the one *producer* currently wired up (see that plugin's own README),
but reaching into it from here would violate the same "convention not
import" boundary this plugin exists to demonstrate — don't.
