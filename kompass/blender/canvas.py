# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Draws the pie on the editor's canvas and takes the pointer.

A draw handler has paint.py draw the pie over Blender's own drawing, and
decides how far each animation has come. Each slot and the dial's centre is
a gizmo that draws nothing, which is how the canvas learns where the pointer
is and gets clicks without a modal operator.
"""

import math
import time
from dataclasses import dataclass, field

import bpy
import gpu

from ..core import layout, model
from . import editor, paint

# Seconds between two frames of an animation.
FRAME = 1 / 60


@dataclass
class _State:
    pointer: tuple[float, float] = (0.0, 0.0)
    # The needle's bearing. A pointer at rest on the centre keeps the last.
    heading: float = 0.0
    # Whether Blender highlights each gizmo, by slot. It highlights none
    # while the pointer is off the canvas, which sends no other sign.
    lit: dict[int, bool] = field(default_factory=dict)
    # The centre's hover state runs from hover_from to hover_target.
    hover_from: float = 0.0
    hover_target: float = 0.0
    hover_since: float = 0.0
    # A pie can arrive under the pointer. Its centre takes the hover state
    # only once the pointer has been outside the ring.
    armed: bool = False
    # The sub-pie slot the pointer rests on, and since when.
    rest: tuple[int, float] | None = None
    # The slot under the pointer when the pie came onto the canvas. It does
    # not open until the pointer has left it.
    held: int | None = None
    opened: float = 0.0
    # The slot the pointer selects, and since when.
    selected: int | None = None
    selected_since: float = 0.0
    # How far each label that is too long for its slot has slid.
    slide: dict[int, float] = field(default_factory=dict)
    drawn: float = 0.0
    look: paint.Look | None = None
    # The pie being left, what it shrinks to and around which point.
    ghost: paint.Look | None = None
    shrink: float = 1.0
    origin: tuple[float, float] = (0.0, 0.0)


_state = _State()
_handle = None


def register():
    global _handle
    _handle = bpy.types.SpaceNodeEditor.draw_handler_add(
        _draw, (), "WINDOW", "POST_PIXEL"
    )


def unregister():
    bpy.types.SpaceNodeEditor.draw_handler_remove(_handle, "WINDOW")
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)


def _ring():
    return layout.RING_RADIUS * (layout.SUB_PIE_DIAL if editor.in_sub_pie() else 1)


def _share(since, now, context):
    """Return how much of an animation that began at since is done, 0 to 1."""
    if context.preferences.view.use_reduce_motion:
        return 1.0
    return min(1.0, (now - since) / layout.MOTION)


def _hover(inside, now, context):
    """Return how far the centre is into its hover state, 0 to 1."""
    state = _state
    step = _share(state.hover_since, now, context)
    hover = layout.toward(state.hover_from, state.hover_target, step)
    if inside != state.hover_target:
        # It turns around from wherever it is.
        state.hover_from, state.hover_target = hover, float(inside)
        state.hover_since = now
    return hover


def _widths(shown):
    return [width for _, _, width in paint.labels(shown)]


def _arrive(shown, depth, now):
    """Start the opening of a pie that was not on the canvas at the last draw."""
    state = _state
    before = state.look
    if before is not None and (before.pie.id, before.depth) == (shown.id, depth):
        return
    state.opened = now
    state.rest = None
    state.armed = False
    state.hover_from = state.hover_target = 0.0
    state.held = layout.slot_under(*state.pointer, _widths(shown))
    # The pie being left keeps the old one.
    state.slide = {}
    state.ghost = None
    if before is not None and depth == before.depth + 1:
        state.ghost = before
        state.shrink, state.origin = layout.PARENT_SHRINK, state.pointer
    elif before is not None and depth == before.depth - 1:
        state.ghost = before
        state.shrink, state.origin = layout.SUB_PIE_SHRINK, (0.0, 0.0)


def _draw():
    context = bpy.context
    if context.space_data.tree_type != editor.KompassTree.bl_idname:
        return
    state = _state
    now = time.perf_counter()
    canvas = paint.Canvas(context)
    gpu.state.blend_set("ALPHA")
    # The whole region, which the pie's centre is not the middle of.
    left, bottom = canvas.units((0, 0))
    right, top = canvas.units(canvas.size)
    corners = [(left, bottom), (right, bottom), (right, top), (left, top)]
    canvas.fill(corners, paint.GROUND)
    shown = editor.shown()
    if shown is None:
        canvas.text("NO PIES", 0, 0, 12, paint.STONE)
        state.look = None
        return
    _arrive(shown, editor.depth(), now)
    pointer = state.pointer if any(state.lit.values()) else None
    inside = pointer is not None and math.hypot(*pointer) <= _ring()
    # Blender drops the highlight during a click, which is not leaving.
    state.armed = state.armed or (pointer is not None and not inside)
    hover = _hover(inside and state.armed, now, context)
    filling = None
    if state.rest is not None:
        slot, since = state.rest
        filling = slot, min(1.0, (now - since) / layout.HOVER_DELAY)
    labels = paint.labels(shown)
    sliding = _slide(labels, pointer, now, context)
    look = paint.Look(
        shown,
        editor.depth(),
        pointer,
        state.heading,
        hover,
        filling,
        labels,
        dict(state.slide),
    )
    opened = _share(state.opened, now, context)
    if state.ghost is not None and opened < 1:
        left = layout.ease_out(1 - opened)
        canvas.opacity = left
        canvas.zoom = state.shrink + (1 - state.shrink) * left
        canvas.origin = state.origin
        paint.draw(canvas, state.ghost, 1.0)
        canvas.zoom, canvas.origin = 1.0, (0.0, 0.0)
    paint.draw(canvas, look, layout.ease_out(opened))
    state.look = look
    moving = opened < 1 or hover != state.hover_target or state.rest is not None
    moving = moving or sliding
    if moving and not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=FRAME)


def _slide(labels, pointer, now, context):
    """Move the labels that are too long. Return whether one is not at rest."""
    state = _state
    selected = None if pointer is None else layout.slot_at(*pointer, _ring())
    if selected != state.selected:
        state.selected, state.selected_since = selected, now
    # A draw after a long rest is not a long step.
    step = min(0.05, now - state.drawn)
    state.drawn = now
    sliding = False
    for slot, (_, text_width, width) in enumerate(labels):
        over = text_width - (width - 2 * layout.LABEL_PAD)
        if over <= 0:
            continue
        held = now - state.selected_since if slot == selected else None
        if context.preferences.view.use_reduce_motion:
            waited = held is not None and held > layout.LABEL_WAIT
            offset = over if waited else 0.0
        else:
            offset = layout.slide(state.slide.get(slot, 0.0), over, held, step)
        state.slide[slot] = offset
        sliding = sliding or (offset < over if slot == selected else offset > 0)
    return sliding


def _tick():
    """Draw the next frame of an animation, and open a sub-pie that is due."""
    state = _state
    if state.rest is not None:
        slot, since = state.rest
        if not any(state.lit.values()):
            state.rest = None
        elif time.perf_counter() - since >= layout.HOVER_DELAY:
            state.rest = None
            editor.click(slot)
    editor.redraw(bpy.context)


def _follow(context, location):
    """Record where the pointer is and return it in canvas units."""
    state = _state
    pointer = paint.Canvas(context).units(location)
    if pointer != state.pointer:
        state.pointer = pointer
        if math.hypot(*pointer) >= layout.NEEDLE_REST:
            state.heading = layout.bearing_to(*pointer)
        _rest(pointer)
        context.region.tag_redraw()
    return pointer


def _rest(pointer):
    """Note the sub-pie slot the pointer came to rest on, if any."""
    state = _state
    shown = editor.shown()
    under = None if shown is None else layout.slot_under(*pointer, _widths(shown))
    if under != state.held:
        state.held = None
    opens = (
        shown is not None
        and under is not None
        and under != state.held
        and isinstance(shown.slots[under], model.SubPieSlot)
    )
    if not opens:
        state.rest = None
    elif state.rest is None or state.rest[0] != under:
        state.rest = under, time.perf_counter()


class _Part:
    """A gizmo that draws nothing and takes a click itself.

    With a target operator instead, Blender shows that operator's tooltip
    over the canvas.
    """

    def draw(self, _context):
        _state.lit[self.slot] = self.is_highlight

    def invoke(self, _context, _event):
        return {"RUNNING_MODAL"}

    def modal(self, _context, _event, _tweak):
        return {"RUNNING_MODAL"}

    def exit(self, context, cancel):
        if not cancel:
            editor.click(self.slot)
            context.region.tag_redraw()


class KOMPASS_GT_slot(_Part, bpy.types.Gizmo):
    bl_idname = "KOMPASS_GT_slot"

    __slots__ = ("slot",)

    def test_select(self, context, location):
        pointer = _follow(context, location)
        return 0 if layout.slot_at(*pointer, _ring()) == self.slot else -1


class KOMPASS_GT_dial(_Part, bpy.types.Gizmo):
    """The centre of the dial, which takes the click that goes back."""

    bl_idname = "KOMPASS_GT_dial"

    # What editor.click takes for the dial.
    slot = -1

    def test_select(self, context, location):
        pointer = _follow(context, location)
        return 0 if math.hypot(*pointer) <= _ring() else -1


class KOMPASS_GGT_canvas(bpy.types.GizmoGroup):
    bl_idname = "KOMPASS_GGT_canvas"
    bl_label = "Kompass Canvas"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "WINDOW"
    bl_options = {"PERSISTENT"}  # noqa: RUF012

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == editor.KompassTree.bl_idname

    def setup(self, _context):
        for slot in range(len(model.SLOT_DIRECTIONS)):
            self.gizmos.new(KOMPASS_GT_slot.bl_idname).slot = slot
        self.gizmos.new(KOMPASS_GT_dial.bl_idname)
