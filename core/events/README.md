# core/events/

The hook registry and the in-memory event bus. No PySide6/Qt imports
here — deliberately not `QObject`s, so `core/` stays importable and
testable without a `QApplication`.

- `hooks.py` — `AppLifecycleContext`/`AppLifecycleHooks`: a fixed,
  three-point plugin lifecycle (`on_app_start`/`on_repo_changed`/
  `on_app_close`, fired from `interface/main_window.py`), replacing an
  older open-ended `GitHookEvent` pub/sub (14 event keys spanning
  before/after clone/pull/push/commit, fired from `core/vcs/git_service.py`,
  plus these same three) that had zero subscribers anywhere in `plugins/`
  — `core/vcs/git_service.py` fires nothing at all now.
- `bus.py` — `InMemoryEventBus[T]`: generic base (`push`, `entries`,
  `add_listener`, `remove_listener`, `clear`, capped at `max_entries`)
  used by `debug_log.py` below. A `NotificationBus` (`notification_bus.py`)
  variant used to live here too — removed 2026-08-10 when
  `plugins/core/Notification/` was folded back into
  `plugins/core/submit/` (see that plugin's README's "Commit history
  panel") and nothing else had ever produced/consumed it.
- `debug_log.py` — `DebugLogEntry`, `DebugLogBus(InMemoryEventBus[DebugLogEntry])`:
  adds `log(source, message)` (push + auto-register the source) and
  `sources()`/`register_source()` for DebugConsole's source filter.
  Consumed by `plugins/core/DebugConsole/`'s live viewer page.

`DebugLogBus` is owned by `core/app_core.py`'s `UkoreCore`
(`core.debug_bus`) and reached via a `core`/`api`
handle — **not** a module-level global. Before the 2026-08-09 reorg it
was a bare-module singleton any code could reach with `import
core.extensibility.debug_log` from anywhere, no handle needed; that was
deliberately given up once it turned out only `launcher.py` and
`interface/plugin_api.py` ever produced entries and only one plugin
ever consumed them — a small enough surface that routing through
`UkoreCore` was worth it for consistency with every other core service. A
plugin needing it reaches it via `PluginAPI.debug_bus`, not by importing
this module directly.
