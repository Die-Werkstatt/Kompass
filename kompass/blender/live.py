# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Opens a stored pie as the pie Kompass draws, in the editor under the pointer.

A modal operator takes every event while the pie is open and a draw handler
has paint.py draw it over the editor.
"""

import math
import time
from dataclasses import dataclass, field

import bpy
import gpu

from ..core import layout, model
from . import paint, pie
from .stage import FRAME, Stage, share

# A shortcut held this long picks the slot it is released on.
HOLD = 0.25


@dataclass
class _Open:
    space: type
    region: bpy.types.Region
    key: str
    # When the pie opened, and once it fades out, when it closed.
    since: float
    # Where in the region the pointer was when the pie opened.
    start: tuple[float, float]
    # The pie on show last, after the pies it was opened from, and where each
    # has its centre in the region.
    trail: list[model.Pie]
    centres: list[tuple[float, float]] = field(default_factory=list)
    stage: Stage = field(default_factory=lambda: Stage(line=True))
    handle: object = None
    timer: object = None
    moving: bool = True

    @property
    def scale(self):
        ui = bpy.context.preferences.system.ui_scale
        size = self.region.width / ui, self.region.height / ui
        return ui * layout.fit(*size, len(self.trail[-1].slots))

    def show(self, shown, x, y):
        """Put a pie on show with its centre at x, y of the region, or as
        near as keeps it inside."""
        self.trail.append(shown)
        scale = self.scale
        size = self.region.width / scale, self.region.height / scale
        centre = layout.keep_in(x / scale, y / scale, size, len(shown.slots))
        self.centres.append((centre[0] * scale, centre[1] * scale))
        self.point(x, y)

    def point(self, x, y):
        """Tell the stage where the pointer is. Return whether it moved."""
        centre, scale = self.centres[-1], self.scale
        pointer = (x - centre[0]) / scale, (y - centre[1]) / scale
        return self.stage.follow(pointer, self.trail[-1], True)


# The pie that is open, or None. Blender shows one at a time.
_open = None
# The pie that fades out after it closed, or None.
_closing = None


def _draw():
    shown = _open or _closing
    if shown is None or bpy.context.region != shown.region:
        return
    gpu.state.blend_set("ALPHA")
    size = shown.region.width, shown.region.height
    canvas = paint.Canvas(size, shown.centres[-1], shown.scale)
    if shown is _closing:
        # A pie that closed before it was drawn has nothing to fade.
        if shown.stage.look is not None:
            left = 1 - share(shown.since, time.perf_counter())
            paint.draw(canvas, shown.stage.look, layout.ease_out(left))
        return
    current = shown.trail[-1]
    shown.stage.disabled = frozenset(
        slot
        for slot, content in enumerate(current.slots)
        if content is not None and not pie.available(bpy.context, content)
    )
    shown.moving = shown.stage.paint(canvas, current, len(shown.trail), True)


def close():
    """Close the open pie, if one is open. It fades out."""
    global _open, _closing
    drop()
    shown, _open = _open, None
    if shown is None:
        return
    bpy.context.window_manager.event_timer_remove(shown.timer)
    _closing = shown
    shown.since = time.perf_counter()
    bpy.app.timers.register(_fade, first_interval=FRAME)
    shown.region.tag_redraw()


def drop():
    """Take the pie that fades out off its editor."""
    global _closing
    shown, _closing = _closing, None
    if shown is None:
        return
    shown.space.draw_handler_remove(shown.handle, "WINDOW")
    if bpy.app.timers.is_registered(_fade):
        bpy.app.timers.unregister(_fade)
    shown.region.tag_redraw()


def _fade():
    """Draw the next frame of the pie that fades out, or take it away."""
    shown = _closing
    done = shown.stage.look is None or share(shown.since, time.perf_counter()) >= 1
    if done:
        drop()
        return None
    shown.region.tag_redraw()
    return FRAME


class KOMPASS_OT_pie_live(bpy.types.Operator):
    """Open a pie that Kompass draws"""

    bl_idname = pie.LIVE
    bl_label = "Open Kompass Pie"
    # Not in operator search: it is useless without a pie id. Blender wants a
    # plain set here.
    bl_options = {"INTERNAL"}  # noqa: RUF012

    pie: bpy.props.StringProperty(name="Pie", options={"HIDDEN", "SKIP_SAVE"})

    def invoke(self, context, event):
        global _open
        stored = pie.find(self.pie)
        if stored is None:
            self.report({"WARNING"}, f'Kompass has no pie "{self.pie}"')
            return {"CANCELLED"}
        area = context.area
        if area is None:
            return {"PASS_THROUGH"}
        # With the pointer on a header or a toolbar the pie still opens.
        region = next(part for part in area.regions if part.type == "WINDOW")
        close()
        drop()
        space = type(context.space_data)
        start = event.mouse_x - region.x, event.mouse_y - region.y
        shown = _Open(space, region, event.type, time.perf_counter(), start, [])
        shown.show(stored, *start)
        shown.handle = space.draw_handler_add(_draw, (), "WINDOW", "POST_PIXEL")
        manager = context.window_manager
        shown.timer = manager.event_timer_add(FRAME, window=context.window)
        _open = shown
        manager.modal_handler_add(self)
        region.tag_redraw()
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        shown = _open
        # Disabling Kompass closes the pie under a running operator.
        if shown is None:
            return {"CANCELLED"}
        at = event.mouse_x - shown.region.x, event.mouse_y - shown.region.y
        if event.type == "TIMER":
            slot = shown.stage.due()
            if slot is not None:
                self._enter(shown, slot)
            if slot is not None or shown.moving:
                shown.region.tag_redraw()
        elif event.type == "MOUSEMOVE":
            if shown.point(*at):
                shown.region.tag_redraw()
        elif event.value == "PRESS" and event.type in {"ESC", "RIGHTMOUSE"}:
            return self._back(shown, at)
        elif event.value == "PRESS" and event.type == "LEFTMOUSE":
            return self._pick(context, shown, at, True)
        elif event.value == "RELEASE" and event.type == shown.key:
            # A pie that was moved off the edge may lie under a pointer that
            # has not moved.
            held = time.perf_counter() - shown.since >= HOLD
            if held and math.dist(at, shown.start) > layout.DRAG_START:
                return self._pick(context, shown, at, False)
        return {"RUNNING_MODAL"}

    def _enter(self, shown, slot):
        """Show the sub-pie of that slot, centred on the pointer."""
        centre, scale = shown.centres[-1], shown.scale
        x, y = (centre[axis] + shown.stage.pointer[axis] * scale for axis in (0, 1))
        shown.show(pie.find(shown.trail[-1].slots[slot].pie), x, y)

    def _back(self, shown, at):
        """Go back to the pie this one was opened from, or close the first."""
        if len(shown.trail) == 1:
            close()
            return {"CANCELLED"}
        shown.trail.pop()
        shown.centres.pop()
        shown.point(*at)
        shown.region.tag_redraw()
        return {"RUNNING_MODAL"}

    def _pick(self, context, shown, at, click):
        """Take a click, or the release of the shortcut, at that place."""
        shown.point(*at)
        pointer, current = shown.stage.pointer, shown.trail[-1]
        dial = layout.SUB_PIE_DIAL if len(shown.trail) > 1 else 1
        if math.hypot(*pointer) <= layout.RING_RADIUS * dial:
            # Letting go of the keys on the dial leaves the pie open for a click.
            return self._back(shown, at) if click else {"RUNNING_MODAL"}
        widths = [width for _, _, width in paint.labels(current)]
        slot = layout.slot_picked(*pointer, widths)
        content = None if slot is None else current.slots[slot]
        if isinstance(content, model.SubPieSlot):
            self._enter(shown, slot)
            shown.region.tag_redraw()
            return {"RUNNING_MODAL"}
        if slot in shown.stage.disabled:
            return {"RUNNING_MODAL"}
        close()
        if content is None:
            return {"CANCELLED"}
        if not pie.run(context, content):
            self.report(
                {"WARNING"}, f'"{paint.label(context, content)}" cannot run here'
            )
        return {"FINISHED"}
