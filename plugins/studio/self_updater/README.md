# plugins/studio/self_updater/

Moves UkoreHub's own self-update check off `MainWindow` and onto the
hook/registry extensibility system, as a worked example of a plugin
contributing to Sidebar's footer.

- `plugin.py` — `register(api)` builds the "Update and Restart" button
  (hidden until an update is found), registers it via
  `api.register_sidebar_footer_action(...)`
  (`interface/sidebar_footer_action_registry.py`), and subscribes
  `_on_app_started` to `GitHookEvent.APP_STARTED`
  (`core/extensibility/hooks.py`) — fired once by `MainWindow` right after
  login + `_build_main_ui()` complete. `_on_app_started` spins up a
  `_UpdateCheckWorker` (`QThread`, moved here from `MainWindow`'s old
  `UpdateCheckWorker`) that calls `core/self_update.py`'s
  `check_for_update()` and toggles the button's visibility. Clicking it
  calls `self_update.pull_update()` then restarts the process via
  `os.execv` (the same mechanism `MainWindow._restart_app` uses for
  Settings > Common's plain Restart button — duplicated inline here since
  that's a private `MainWindow` method this plugin has no handle on).

Settings > Common's plain "Restart" button is unrelated to this plugin and
stays in `interface/main_window.py`.
