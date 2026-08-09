# core/events/

The hook registry and the two in-memory event buses. No PySide6/Qt imports
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
  shared by the two buses below.
- `debug_log.py` — `DebugLogEntry`, `DebugLogBus(InMemoryEventBus[DebugLogEntry])`:
  adds `log(source, message)` (push + auto-register the source) and
  `sources()`/`register_source()` for DebugConsole's source filter.
  Consumed by `plugins/core/DebugConsole/`'s live viewer page.
- `notification_bus.py` — `NotificationEntry`,
  `NotificationBus(InMemoryEventBus[NotificationEntry])`: overrides `push()`
  to build the entry from individual fields (`source`, `project_id`,
  `repo_id`, `label`, ...) instead of taking a pre-built one, and adds
  `entries_for(project_id, repo_id)` (project-wide entries plus entries
  scoped to one repo, newest first). Consumed by `plugins/core/Notification/`'s
  tab.

Both buses are owned by `core/app_core.py`'s `UkoreCore`
(`core.debug_bus`, `core.notification_bus`) and reached via a `core`/`api`
handle — **not** a module-level global. Before the 2026-08-09 reorg these
were bare-module singletons any code could reach with `import
core.extensibility.debug_log` from anywhere, no handle needed; that was
deliberately given up once it turned out only `launcher.py` and
`interface/plugin_api.py` ever produced entries and only one plugin each
ever consumed them — a small enough surface that routing through
`UkoreCore` was worth it for consistency with every other core service. A
plugin needing either bus reaches it via `PluginAPI.debug_bus`/
`.notification_bus`, not by importing this module directly.
