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
from .stage import FRAME, Stage


@dataclass
class _Input:
    # Whether Blender highlights each gizmo, by slot. It highlights none
    # while the pointer is off the canvas, which sends no other sign.
    lit: dict[int, bool] = field(default_factory=dict)
    # The slot a press began on and where. Once it is dragged: its pie's id,
    # its index and its label.
    pressed: tuple | None = None
    dragged: tuple | None = None
    # Since when a dragged slot is held on a sub-pie's dial.
    back: float | None = None


_stage = Stage()
_input = _Input()
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


def _count():
    """Return how many slots the pie on the canvas has."""
    shown = editor.shown()
    return model.NATIVE_SLOTS if shown is None else len(shown.slots)


def _ring():
    return layout.RING_RADIUS * (layout.SUB_PIE_DIAL if editor.in_sub_pie() else 1)


def _widths(shown):
    return [width for _, _, width in paint.labels(shown)]


def _draw():
    context = bpy.context
    if context.space_data.tree_type != editor.KompassTree.bl_idname:
        return
    canvas = paint.fitted(context, _count())
    gpu.state.blend_set("ALPHA")
    # The whole region, which the pie's centre is not the middle of.
    left, bottom = canvas.units((0, 0))
    right, top = canvas.units(canvas.size)
    corners = [(left, bottom), (right, bottom), (right, top), (left, top)]
    canvas.fill(corners, paint.BLACK)
    shown = editor.shown()
    if shown is None:
        canvas.text("NO PIES", 0, 0, 12, paint.STONE)
        _stage.look = None
        return
    on = any(_input.lit.values())
    moving = _stage.paint(canvas, shown, editor.depth(), on, editor.selected())
    if _input.dragged is not None and on:
        paint.draw_carried(canvas, _stage.look, _input.dragged[2])
    if moving and not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=FRAME)


def _tick():
    """Draw the next frame of an animation, and open a sub-pie that is due."""
    if not any(_input.lit.values()):
        _stage.rest = None
    if _input.back is not None:
        if time.perf_counter() - _input.back < layout.BACK_DELAY:
            return FRAME
        # A dragged slot is taken back to the pie this one was opened from.
        _input.back = None
        editor.click(-1)
    slot = _stage.due()
    if slot is not None and _input.dragged is not None:
        # A dragged slot is taken into the sub-pie it rests on.
        editor.enter(slot)
    elif slot is not None:
        editor.click(slot)
    editor.redraw(bpy.context)


def _follow(context, location):
    """Record where the pointer is and return it in canvas units."""
    pointer = paint.fitted(context, _count()).units(location)
    opening = editor.preview or _input.dragged is not None
    if _stage.follow(pointer, editor.shown(), opening):
        context.region.tag_redraw()
    return pointer


class _Part:
    """A gizmo that draws nothing and takes a click itself.

    With a target operator instead, Blender shows that operator's tooltip
    over the canvas.
    """

    def draw(self, _context):
        _input.lit[self.slot] = self.is_highlight

    def _near(self):
        """Return the slot the pointer is close to, -1 on the dial."""
        if self.slot < 0:
            return -1
        # Blender picks the gizmo by bearing at any distance; a click
        # counts only close to a slot.
        return layout.slot_clicked(*_stage.pointer, _widths(editor.shown()))

    def invoke(self, _context, _event):
        slot = self._near()
        _input.pressed = None
        held = slot is not None and slot >= 0 and editor.shown().slots[slot]
        if held and not editor.preview:
            _input.pressed = slot, _stage.pointer
        return {"RUNNING_MODAL"}

    def modal(self, context, event, _tweak):
        pointer = _follow(context, (event.mouse_region_x, event.mouse_region_y))
        if _input.pressed is not None:
            slot, start = _input.pressed
            moved = math.dist(pointer, start) > layout.DRAG_START
            if moved and _input.dragged is None:
                label = _stage.look.labels[slot][0]
                _input.dragged = editor.shown().id, slot, label
                # Its own sub-pie does not open under it.
                _stage.held = slot
        held = _input.dragged is not None and editor.in_sub_pie()
        if not (held and math.hypot(*pointer) <= _ring()):
            _input.back = None
        elif _input.back is None:
            _input.back = time.perf_counter()
            if not bpy.app.timers.is_registered(_tick):
                bpy.app.timers.register(_tick, first_interval=FRAME)
        return {"RUNNING_MODAL"}

    def exit(self, context, cancel):
        dragged, _input.dragged, _input.pressed = _input.dragged, None, None
        _input.back = None
        if cancel:
            return
        slot = self._near()
        if dragged is None:
            editor.click(slot)
        elif slot not in (None, -1) and dragged[:2] != (editor.shown().id, slot):
            editor.select(dragged[1], dragged[0])
            bpy.ops.kompass.slot_swap(other=slot)
        editor.redraw(context)


class KOMPASS_GT_slot(_Part, bpy.types.Gizmo):
    bl_idname = "KOMPASS_GT_slot"

    __slots__ = ("slot",)

    def test_select(self, context, location):
        pointer = _follow(context, location)
        return 0 if layout.slot_at(*pointer, _count(), _ring()) == self.slot else -1


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
        for slot in range(model.WIDE_SLOTS):
            self.gizmos.new(KOMPASS_GT_slot.bl_idname).slot = slot
        self.gizmos.new(KOMPASS_GT_dial.bl_idname)
