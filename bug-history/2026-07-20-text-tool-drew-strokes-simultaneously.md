# Repositioning a text box also drew a brush stroke at the same time

## Symptom

In UkoreShot's Edit Video dialog, dragging a text annotation into position
(or otherwise interacting with one) could also leave a freehand stroke on
the canvas at the same time, as if the brush was still active underneath.

## Root cause

`draw_overlay.py`'s `DrawOverlay` only ever tracked one boolean,
`_eraser`, to distinguish brush from eraser — "Text" was not a mode at
all. The toolbar's Text tool button was wired to a one-shot
`DrawOverlay.add_text_box()` action (`clicked`, not `toggled`), so
clicking it added a text box but left whichever of Brush/Eraser was
already checked (Brush, by default) fully active — `_drawing_enabled`
stayed `True` and `_eraser` stayed whatever it was. Since drawing was
never actually disabled while working with text boxes, any mouse
interaction that landed on the `DrawOverlay` canvas itself (rather than
being fully consumed by a `_TextBoxItem` child widget) could start or
continue a stroke at the same time.

## Fix

`draw_overlay.py`: replaced the single `_eraser: bool` with `_tool`, one
of module-level `TOOL_BRUSH`/`TOOL_ERASER`/`TOOL_TEXT` (`set_tool`
replaces `set_eraser_mode`). Every mouse handler now branches on `_tool`
explicitly, and the three are mutually exclusive by construction:
`mousePressEvent` places a new text box at the click position and returns
immediately when `_tool == TOOL_TEXT`, never falling through to the
stroke/erase logic; `mouseMoveEvent`/`mouseReleaseEvent` do the same. The
"F" resize gesture is also disabled while `_tool == TOOL_TEXT` (size
doesn't apply to placing a text box). `player_widget.py`: `text_tool_button`
became a third checkable member of the same `QButtonGroup` as
Brush/Eraser (was previously not checkable at all), each button's
`toggled(True)` now calls `DrawOverlay.set_tool(...)` directly. Also added
`core/theme.py`'s `QToolButton:checked` rule (accent-colored fill) so the
active tool is visually unambiguous, which the checked-but-unstyled
buttons hadn't provided before either.

## Lesson

**A "one boolean flag" model for tool state stops being correct the
moment a third tool is added, even if that third tool is wired up as a
plain one-shot button instead of an explicit mode.** The bug wasn't in
the new Text feature's own code — it was that adding Text without also
converting the existing brush/eraser boolean into a real exclusive
enum/state left the *old* tools still fully active underneath the new
one. When adding a new mode next to an existing binary toggle, check
whether the toggle itself needs to become a proper multi-value state
first, not just whether the new mode's own handler is correct in
isolation.
