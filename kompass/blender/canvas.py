# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Draws the pie on the editor's canvas and takes the pointer.

The dial is drawn behind Blender's gizmos by a draw handler. Each slot and
the dial's centre is a gizmo, which is how the canvas learns where the
pointer is and gets clicks without a modal operator.
"""

import math

import blf
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from ..core import layout, model
from . import editor, pie, storage, tools

# The brand colours of docs/brand/README.md.
GROUND = (0.055, 0.055, 0.055, 1)
LINE = (0.173, 0.173, 0.173, 1)
STONE = (0.561, 0.553, 0.533, 1)
INK = (0.945, 0.941, 0.925, 1)
SIGNAL = (0.949, 0.329, 0.176, 1)
WHITE = (1, 1, 1, 1)

# Blender's own interface font.
FONT = 0

# The pointer in canvas units, and the needle's bearing. A pointer at rest
# on the centre keeps the last bearing.
_pointer = (0.0, 0.0)
_heading = 0.0
_handle = None


def register():
    global _handle
    _handle = bpy.types.SpaceNodeEditor.draw_handler_add(
        _draw_dial, (), "WINDOW", "BACKDROP"
    )


def unregister():
    bpy.types.SpaceNodeEditor.draw_handler_remove(_handle, "WINDOW")


class _Canvas:
    """Turns canvas units into the pixels of a region."""

    def __init__(self, context):
        region = context.region
        self.size = region.width, region.height
        # The sidebar lies over the right of the canvas.
        sidebar = next(r for r in context.area.regions if r.type == "UI")
        width = region.width - (sidebar.width if sidebar.width > 1 else 0)
        scale = context.preferences.system.ui_scale
        self.scale = scale * layout.fit(width / scale, region.height / scale)
        self.centre = width / 2, region.height / 2
        dial = layout.SUB_PIE_DIAL if editor.in_sub_pie() else 1
        self.dial = layout.DIAL_RADIUS * dial
        self.ring = layout.RING_RADIUS * dial

    def pixels(self, points, bearing=0):
        """Return the points in pixels, turned clockwise around the centre."""
        angle = math.radians(bearing)
        sin, cos = math.sin(angle), math.cos(angle)
        return [
            (
                self.centre[0] + (x * cos + y * sin) * self.scale,
                self.centre[1] + (y * cos - x * sin) * self.scale,
            )
            for x, y in points
        ]

    def units(self, location):
        return (
            (location[0] - self.centre[0]) / self.scale,
            (location[1] - self.centre[1]) / self.scale,
        )

    def fill(self, points, colour, bearing=0):
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.uniform_float("color", colour)
        batch = batch_for_shader(
            shader, "TRI_FAN", {"pos": self.pixels(points, bearing)}
        )
        batch.draw(shader)

    def line(self, points, colour, width):
        shader = gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")
        shader.uniform_float("viewportSize", self.size)
        shader.uniform_float("lineWidth", width * self.scale)
        shader.uniform_float("color", colour)
        batch_for_shader(shader, "LINE_STRIP", {"pos": self.pixels(points)}).draw(
            shader
        )

    def text(self, text, x, y, size, colour, width=None):
        """Draw text centred on x with its baseline at y."""
        blf.size(FONT, size * self.scale)
        blf.color(FONT, *colour)
        ((left, bottom),) = self.pixels([(x, y)])
        text_width = blf.dimensions(FONT, text)[0]
        if width is not None and text_width > width * self.scale:
            half = width * self.scale / 2
            blf.enable(FONT, blf.CLIPPING)
            blf.clipping(
                FONT, left - half, bottom - size, left + half, bottom + 2 * size
            )
            text_width = width * self.scale
        blf.position(FONT, left - text_width / 2, bottom, 0)
        blf.draw(FONT, text)
        blf.disable(FONT, blf.CLIPPING)


def _mix(a, b, amount):
    return tuple(x + (y - x) * amount for x, y in zip(a, b))


def _draw_dial():
    context = bpy.context
    if context.space_data.tree_type != editor.KompassTree.bl_idname:
        return
    canvas = _Canvas(context)
    gpu.state.blend_set("ALPHA")
    # The whole region, which the pie's centre is not the middle of.
    left, bottom = canvas.units((0, 0))
    right, top = canvas.units(canvas.size)
    corners = [(left, bottom), (right, bottom), (right, top), (left, top)]
    canvas.fill(corners, GROUND)
    shown = editor.shown()
    if shown is None:
        canvas.text("NO PIES", 0, 0, 12, STONE)
        return
    selected = layout.slot_at(*_pointer, canvas.ring)
    circle = [layout.point(canvas.ring, bearing) for bearing in range(0, 361, 5)]
    canvas.line(circle, LINE, 1.5)
    for bearing, inner, outer, major in layout.ticks(canvas.dial):
        on = selected is not None and bearing == layout.BEARINGS[selected]
        colour = SIGNAL if on else INK if major else (*STONE[:3], 0.55)
        tick = [layout.point(inner, bearing), layout.point(outer, bearing)]
        canvas.line(tick, colour, 3 if on else 2 if major else 1)
    tip = canvas.dial + 16
    canvas.fill([(0, tip), (5, tip - 8), (-5, tip - 8)], SIGNAL, _heading)
    length, half = canvas.dial - 22, canvas.dial * 0.15
    canvas.fill([(0, length), (half, 3), (-half, 3)], SIGNAL, _heading)
    canvas.fill([(-half, -3), (half, -3), (0, -length)], INK, _heading)
    inside = math.hypot(*_pointer) <= canvas.ring
    below = "BACK" if editor.in_sub_pie() else "CLOSE"
    canvas.text(below, 0, -canvas.ring - 26, 11, INK if inside else (*STONE[:3], 0.6))
    if editor.in_sub_pie():
        canvas.text(shown.name.upper(), 0, canvas.ring + 14, 12, INK)


def _follow(context, location):
    """Record where the pointer is and return it in canvas units."""
    global _pointer, _heading
    canvas = _Canvas(context)
    pointer = canvas.units(location)
    if pointer != _pointer:
        _pointer = pointer
        if math.hypot(*pointer) >= layout.NEEDLE_REST:
            _heading = layout.bearing_to(*pointer)
        context.region.tag_redraw()
    return canvas, pointer


class _Clickable:
    """A gizmo that takes a click itself.

    With a target operator instead, Blender shows that operator's tooltip
    over the canvas.
    """

    def invoke(self, _context, _event):
        return {"RUNNING_MODAL"}

    def modal(self, _context, _event, _tweak):
        return {"RUNNING_MODAL"}

    def exit(self, context, cancel):
        if not cancel:
            editor.click(self.slot)
            context.region.tag_redraw()


class KOMPASS_GT_slot(_Clickable, bpy.types.Gizmo):
    bl_idname = "KOMPASS_GT_slot"

    __slots__ = ("slot",)

    def test_select(self, context, location):
        canvas, pointer = _follow(context, location)
        return 0 if layout.slot_at(*pointer, canvas.ring) == self.slot else -1

    def draw(self, context):
        shown = editor.shown()
        if shown is None:
            return
        canvas = _Canvas(context)
        gpu.state.blend_set("ALPHA")
        content = shown.slots[self.slot]
        amount = layout.highlight(*_pointer, self.slot, canvas.ring)
        left, bottom = layout.slot_corner(self.slot)
        right, top = left + layout.SLOT_WIDTH, bottom + layout.SLOT_HEIGHT
        box = [(left, bottom), (right, bottom), (right, top), (left, top)]
        canvas.fill(box, _mix(GROUND, SIGNAL, amount))
        canvas.line([*box, box[0]], _mix(LINE, SIGNAL, amount), 1)
        if content is None:
            return
        if isinstance(content, model.SubPieSlot):
            marker = [(right - 9, top), (right, top), (right, top - 9)]
            canvas.fill(marker, INK if amount > 0.6 else SIGNAL)
        canvas.text(
            _label(context, content).upper(),
            (left + right) / 2,
            bottom + layout.SLOT_HEIGHT / 2 - 4,
            12,
            _mix(INK, WHITE, amount),
            layout.SLOT_WIDTH - 12,
        )


class KOMPASS_GT_dial(_Clickable, bpy.types.Gizmo):
    """The centre of the dial, which takes the click that goes back."""

    bl_idname = "KOMPASS_GT_dial"

    # What editor.click takes for the dial.
    slot = -1

    def test_select(self, context, location):
        canvas, pointer = _follow(context, location)
        return 0 if math.hypot(*pointer) <= canvas.ring else -1

    def draw(self, context):
        # _draw_dial draws the dial, behind the slots.
        pass


def _label(context, slot):
    if slot.label:
        return slot.label
    if isinstance(slot, model.ToolSlot):
        name = tools.label(context, slot.space_type, slot.tool)
        return name or slot.tool.rpartition(".")[2].replace("_", " ")
    if isinstance(slot, model.OperatorSlot):
        operator = pie.operator_type(slot.idname)
        return slot.idname if operator is None else operator.name
    return next(stored.name for stored in storage.pies if stored.id == slot.pie)


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
