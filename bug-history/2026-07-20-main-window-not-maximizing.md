# Main window not maximizing on launch

## Symptom

UkoreHub sometimes came up in a small/"normal" window instead of
maximized, despite the code already calling `showMaximized()` twice (once
in `MainWindow.__init__`, once again in `launcher.py` right before
`app.exec()`) specifically to work around an earlier version of this same
problem.

## Root cause

On the **cached-login path** (returning user, `github_username` + a saved
token already present), `MainWindow.__init__` calls `_build_main_ui()`
synchronously — i.e. it runs *between* the two `showMaximized()` calls,
not after both of them. `_build_main_ui()` had:

```python
self.setMinimumHeight(MAIN_WINDOW_MIN_HEIGHT)
if self.height() < MAIN_WINDOW_MIN_HEIGHT:
    self.resize(self.width(), MAIN_WINDOW_MIN_HEIGHT)
```

At that point the window has never actually been realized on screen (no
native window created yet, no event loop processed), so `self.height()`
reads whatever pre-realization default Qt reports — comfortably under
`MAIN_WINDOW_MIN_HEIGHT` (600) — so `resize()` fires unconditionally on
this path. An explicit `resize()` call between a pending maximized state
and the window's first real show can clobber that pending state on
Windows, undoing what the first `showMaximized()` was trying to set up.
`launcher.py`'s second `showMaximized()` call (the "last step" one) should
in theory override this again — but empirically it didn't always stick,
consistent with Qt/Windows window-state races around geometry calls made
before a window's first real show.

## Fix

Guarded the `resize()` call on `isMaximized()` in
`interface/main_window.py`'s `_build_main_ui`:

```python
if not self.isMaximized() and self.height() < MAIN_WINDOW_MIN_HEIGHT:
    self.resize(self.width(), MAIN_WINDOW_MIN_HEIGHT)
```

## Update 2026-07-20 (same day) — guard alone wasn't sufficient

The `isMaximized()` guard above stopped `_build_main_ui()`'s own `resize()`
from clobbering the maximized state, but the window still came up
minimized/"normal"-sized — icon showing maximized, actual on-screen size
small — on **both** the cached-login path and the fresh-login path (via
`LoginOverlay`). Root cause: **both** `showMaximized()` calls —
`MainWindow.__init__`'s early one and `launcher.py`'s "last step" one —
were being called synchronously, before `app.exec()` runs a single event,
i.e. both still pre-realization. Qt sets the window's *intended* state
(`isMaximized()`) immediately regardless of realization, but on Windows the
real win32 window rect only reliably follows once the native window has
actually been created and shown once — a `showMaximized()` issued before
that can report `isMaximized() == True` (taskbar/title-bar icon already
shows "restore") while the physical window stays small.

First attempted fix — deferring only `launcher.py`'s second call via
`QTimer.singleShot(0, window.showMaximized)` while leaving
`MainWindow.__init__`'s early call in place — **was insufficient**: the
early call in `__init__` already puts the widget into a "shown" state,
so it's the one driving the actual (broken) realization; deferring only
the redundant second call didn't change that.

Actual fix, verified by launching the real app and checking
`GetWindowRect`/`IsZoomed` via the Win32 API (not just reading the code):
**remove `MainWindow.__init__`'s early `showMaximized()`/`show()` call
entirely.** Nothing needs to be visible before `app.exec()` starts — Qt
never actually paints anything until the event loop runs, so building the
whole widget tree first (login gate or full main UI, whichever branch)
and only calling `showMaximized()` **once**, deferred via
`QTimer.singleShot(0, window.showMaximized)` in `launcher.py` right before
`app.exec()`, is what makes it reliably stick. `_build_main_ui()`'s
`isMaximized()` guard (the original Fix above) was kept as defense in
depth even though it's now always `False` at that point (nothing has been
shown yet either way) — see the Lesson.

## Lesson

Don't call `resize()`/`setGeometry()`/`showMaximized()`/similar
window-state APIs on a top-level window and expect them to reliably stick
if they run before `app.exec()` has processed at least one event — Qt
considers the window's *intended* state changed immediately (so
`isMaximized()` reflects it right away), but the actual on-screen/native
geometry on Windows only reliably follows once the window has actually
been shown once. Concretely:
- **Only ever call `show()`/`showMaximized()` once per app launch**, and
  make it the *last* thing that happens, deferred via
  `QTimer.singleShot(0, ...)` so it runs after `app.exec()` starts the
  event loop — not called synchronously "right before `app.exec()`",
  which looks like the last possible moment but isn't the same thing.
- Don't add an "early" `show()`/`showMaximized()` call earlier in startup
  to avoid a perceived flash-of-unstyled-window — nothing is ever painted
  before the event loop runs regardless of when `show()` was *called*, so
  it isn't needed and it's what actually caused this bug twice.
- A `resize()`/geometry call between a pending `showMaximized()` and the
  window's first real show can clobber it — guard with `isMaximized()`
  first, kept in `_build_main_ui()` as defense in depth even though the
  fix above means it's normally moot.
- **Verify a window-state fix by actually launching the app and querying
  `GetWindowRect`/`IsZoomed` (Win32 API) or a screenshot** — reading the
  code and reasoning about it was not enough here; the first attempted fix
  looked correct and wasn't.
This is easy to reintroduce: any future code that adds a `show()`/
`showMaximized()` call anywhere during startup (`MainWindow.__init__`,
`_build_main_ui()`, or `launcher.py`) should go through the single
deferred call above, not add another one.
