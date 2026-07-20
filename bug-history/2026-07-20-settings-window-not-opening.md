# Setting popup silently failed to open

## Symptom

Clicking the app-level **Setting** button (Sidebar footer, icon-only
button right after the GitHub username) did nothing — no window appeared,
no error visible, the rest of the app stayed fully responsive. Reported
across several sessions before the actual cause was found, because static
code review of the button's wiring and even constructing `SettingsDialog`
directly in a headless test both looked completely correct.

## Root cause

`interface/main_window.py`'s `_on_settings_requested` (the button's slot):

```python
dialog = SettingsDialog(self, settings_tab_registry=self.settings_tab_registry)
common_settings_page = dialog.view.get_tab_widget(builtin_settings_tabs.COMMON)
...
dialog.exec()
```

`dialog.view` is a `SettingsView` instance. `SettingsView` never defined a
`get_tab_widget` method — only `SettingsDialog` did, and even that
definition was broken:

```python
class SettingsDialog(QDialog):
    def get_tab_widget(self, key: str) -> QWidget | None:
        return self._tab_widgets.get(key)   # SettingsDialog has no self._tab_widgets — only SettingsView does
```

So `dialog.view.get_tab_widget(...)` raised
`AttributeError: 'SettingsView' object has no attribute 'get_tab_widget'`
— inside a slot invoked directly by a Qt signal (`clicked -> emit ->
_on_settings_requested`). PySide6 doesn't crash the app when a slot raises
this way; it prints the traceback via `sys.excepthook` and the event loop
keeps running. Since the app is normally launched via `pythonw.exe` (no
console attached), that traceback went nowhere visible. Critically, the
exception happened on the line *before* `dialog.exec()` — the dialog
object was fully constructed in memory, just never shown, which is why
there was no visible error AND no dialog: both "the crash" and "the fix
that would show something" were on opposite sides of the same line.

## Fix

Added a real `get_tab_widget` to `SettingsView` (the class that actually
owns `self._tab_widgets`), and had `SettingsDialog.get_tab_widget`
delegate to `self.view.get_tab_widget(key)` instead of reading a
nonexistent attribute on itself. See
`interface/settings/settings_view.py`.

## Lesson

This bug was invisible to every check except actually calling the exact
method the button triggers. Two takeaways:

1. **A headless test that only *constructs* a dialog/page isn't the same
   as calling the handler that uses it.** `SettingsDialog(...)` construction
   succeeded fine on its own — the crash was one line further, in code
   that only runs from inside `_on_settings_requested`. When investigating
   "clicking X does nothing," reproduce the actual call path (call the
   slot method itself, or at minimum replicate every line it runs after
   construction), not just the object construction.
2. **When a method is split across a wrapper class delegating to an inner
   object** (`SettingsDialog` wrapping `SettingsView`, same shape
   `RepoSettingsDialog`/`RepoSettingsPanel` uses), double-check the
   delegate target actually implements the method being delegated to —
   `self._tab_widgets` vs `self.view._tab_widgets` is exactly the kind of
   typo that passes a casual read (both read as "the tab widgets") but
   fails at the attribute level. This kind of bug is also invisible to
   any test that doesn't run via `python launcher.py` with a console
   attached (or a headless repro checking for exceptions explicitly) —
   packaged/`pythonw.exe` runs swallow it completely.
