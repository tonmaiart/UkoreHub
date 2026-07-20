# Draw overlay never received mouse input (two unrelated root causes)

## Symptom

In UkoreShot's Edit Video dialog, the brush tool did nothing — pressing
and dragging on the video produced no strokes at all, not even a partial
line, and (once added) the brush-size hover indicator never appeared
either. This took **three** attempted fixes across two genuinely
different root causes stacked on top of each other — the first fix
(`Qt.WA_AlwaysStackOnTop`) didn't resolve it, and the second fix
(replacing `QVideoWidget`) *fixed the first root cause* but the symptom
persisted because a second, unrelated bug was hiding behind it the whole
time. See "Second root cause" below for how that one was actually found —
`plugins/studio/DebugConsole/` (added specifically for this) turned an
unfalsifiable "still doesn't work" report into a one-line proof.

## Root cause

`player_widget.py`'s `PlayerWidget` stacked `DrawOverlay` (a plain,
translucent `QWidget`) on top of a `QVideoWidget` via
`QStackedLayout(StackAll)`. `QVideoWidget` renders through a real native
OS window handle (platform video backends on Windows bind their
presentation surface to an actual HWND) — native child windows are
Z-ordered and hit-tested by the OS window manager directly, not by Qt's
own widget-stacking logic. `Qt.WA_AlwaysStackOnTop` only affects Qt-level
compositing/paint order for ordinary (non-native) sibling widgets; it
cannot move a genuinely separate native window's real OS Z-order. So the
video's native surface kept swallowing every mouse press meant for
`DrawOverlay`, regardless of that attribute or of `DrawOverlay` being
added to the layout after (i.e. logically "on top of") the video widget.

## Fix

`player_widget.py`: replaced `QVideoWidget` entirely with a new
`_VideoSurface(QWidget)` that has no native window at all — it paints the
current frame itself via `QPainter.drawImage`, fed by
`QMediaPlayer.setVideoSink(QVideoSink)` + `QVideoSink.videoFrameChanged`
converting each `QVideoFrame` to a `QImage` via `.toImage()`. This is the
exact same frame-grab mechanism `thumbnail_loader.py` already used
(successfully) for its one-shot thumbnails — just applied continuously
instead of once. With no native window in the stack, `DrawOverlay` now
gets normal, correctly-ordered mouse events like any other pair of
sibling widgets, and `Qt.WA_AlwaysStackOnTop` was left on `DrawOverlay`
as a no-longer-load-bearing but harmless leftover.

## Second root cause: `QStackedLayout(StackAll)` left `DrawOverlay` non-visible

After the `_VideoSurface` fix above, the user reported the brush *still*
didn't work, and the new hover-size circle never appeared either — with
no way to tell, from the outside, whether the fix had even taken effect
(the app is normally launched via `pythonw.exe`, no console) or whether a
second bug was in play. `plugins/studio/DebugConsole/` +
`core/extensibility/debug_log.py` were added specifically to answer that:
`draw_overlay.py`'s `mousePressEvent`/`mouseMoveEvent`/`resizeEvent` were
instrumented to log to a `"UkoreShot.Draw"` source, viewable live in-app.

The very first real-app log line proved it: `resizeEvent, new size=(860,
500), visible=False` — `DrawOverlay` had correct, non-zero geometry but
`isVisible()` was `False`, and across ten full seconds of the user
hovering/dragging, not one `mousePressEvent`/`mouseMoveEvent` log line
ever appeared. `QStackedLayout(StackAll)` (still used to stack
`DrawOverlay` over `_VideoSurface` at that point) was not making the
non-current widget visible/interactive the way its documented `StackAll`
semantics suggest it should — something about this specific layout usage
was silently defeating it.

**Fix:** `player_widget.py` — replaced `QStackedLayout(StackAll)` with a
new `_VideoStack(QWidget)` that manages the two widgets by hand:
`setParent`, unconditional `.show()` on both, and `.setGeometry(0, 0, w,
h)` + `overlay.raise_()` on every resize. No layout, no stacking-mode
semantics to get subtly wrong — just two sibling widgets with explicit
geometry and explicit Z-order, which Qt resolves for mouse hit-testing
exactly the way `.raise_()`'s own docs describe. Verified headlessly
(offscreen `QApplication`, widget embedded in a shown `QDialog`):
`draw_overlay.isVisible()` is `True` and its geometry matches
`video_surface`'s exactly, which was not true before this fix.

## Lesson

**A Qt widget attribute set on widget A can never override native-window
Z-ordering of a *different* native widget B it's stacked against** — if a
mouse-interactive overlay needs to sit on top of a `QVideoWidget` (or any
other widget documented as using a native surface — `QOpenGLWidget`,
`QAxWidget`, etc.), don't reach for `WA_AlwaysStackOnTop`/`raise_()` on
the overlay first; check whether the native widget can be replaced with a
non-native equivalent instead (here: `QVideoSink` + manual paint, mirrored
from this exact codebase's own `thumbnail_loader.py`). If a symptom is
"mouse events never arrive at all" (not just "paints in the wrong order"),
suspect a native-window Z-order conflict specifically, not a Qt-level
stacking-attribute problem.

**Separately: don't trust `QStackedLayout(StackAll)` to make every
stacked widget visible/interactive without checking `isVisible()`
directly** — its documented behavior didn't match what actually happened
here, and a plain `print`/log statement checking `isVisible()` and
geometry immediately exposed it, where guessing at more Qt-attribute
fixes (as the first two attempts did) would not have. **When a bug report
says "still doesn't work" and you cannot interactively reproduce the UI
yourself, add cheap, structured, in-app instrumentation before guessing
again** — `core/extensibility/debug_log.py` +
`plugins/studio/DebugConsole/` turned a third round of blind guessing
into a one-line proof of the actual defect. Prefer two independent,
directly-observable facts (widget visibility + event delivery) over a
plausible-sounding theory that can't be checked from where you're
sitting.
