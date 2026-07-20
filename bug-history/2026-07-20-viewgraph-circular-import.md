# Viewgraph disappeared (circular import)

## Symptom

The Viewgraph (Project Editor's node-graph panel — always-docked beside
whichever section is showing) vanished from the app entirely after a
Repository Setting reorganization change. The rest of the app kept
running normally; there was no crash dialog or visible error (running via
`pythonw.exe`, no console).

## Root cause

`plugins/studio/project_editor/repo_settings_panel.py` added
`from plugins.studio.project_editor.plugin import CUSTOM_PATHS_SETTINGS_KEY`
to classify Repository Setting's tabs. But the plugin's own import chain
already ran the other way:

```
plugin.py
  -> imports project_editor_page.py (ProjectEditorPage)
    -> imports project_graph_view.py (ProjectGraphView)
      -> imports repo_settings_panel.py (RepoSettingsDialog)
        -> imports plugin.py   <-- plugin.py is still mid-import here
```

Python import machinery can't resolve `plugin.py` a second time while it's
still executing its own top-level code (it's "partially initialized") — the
`from plugins.studio.project_editor.plugin import CUSTOM_PATHS_SETTINGS_KEY`
line raised `ImportError: cannot import name 'ProjectEditorPage' from
partially initialized module ...` (the error surfaces confusingly on
whatever name the *original* importer wanted, not on the new import that
actually caused the cycle).

This exception happened during plugin discovery/loading
(`core/extensibility/loader.py`'s `discover_plugins`/`apply_plugins`), which
catches per-plugin import failures and just logs them
(`print(f"UkoreHub: plugin at '...' failed to load: ...")`) rather than
crashing the app — so `project_editor` silently never registered its
section at all, and the rest of the app came up fine without it.

## Fix

`repo_settings_panel.py` no longer imports the constant from `plugin.py` —
the one string value (`"project_editor_custom_paths"`) is duplicated
locally with a comment explaining why, breaking the cycle. See
`plugins/studio/project_editor/repo_settings_panel.py`'s
`_CUSTOM_PATHS_SETTINGS_KEY`.

## Lesson

Before adding a new top-level `from plugins.studio.<Name>.<module> import
X` inside any file under `plugins/studio/<Name>/`, check whether
`<Name>`'s own `plugin.py` (the entry point) already imports — directly or
transitively — the file you're editing. If it does, importing `plugin.py`
(or anything that itself imports `plugin.py`) from that file closes a
cycle, even though neither file imports the other *directly*. A plain
string/constant is almost never worth risking this — duplicate the literal
value with a comment instead of reaching across the plugin's own import
graph. This class of failure is easy to miss in review (it only breaks at
plugin-load time, not at edit time) and is silent in production (logged to
a console the packaged app usually doesn't have) — the only reliable way
to catch it is to actually run plugin discovery, e.g. via a headless
repro of `launcher.py`'s startup sequence (construct
`QApplication(offscreen)` + `discover_plugins`/`apply_plugins` against a
scratch copy of `data/`, check `discovery.failures`/`plugin_apply_failures`
for the plugin you touched) — see root `CLAUDE.md`'s "Headless/smoke
testing" section for the scratch-data-only rule.
