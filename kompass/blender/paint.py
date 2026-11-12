# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Draws one pie as it looks at one moment."""

import math
from dataclasses import dataclass

import blf
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from ..core import layout, model
from . import pie, storage, tools

# The colours of docs/brand/README.md and docs/design/README.md.
# The editor's canvas, and a slot on it or over a viewport.
BLACK = (0, 0, 0, 1)
GROUND = (0.055, 0.055, 0.055, 1)
LINE = (0.173, 0.173, 0.173, 1)
STONE = (0.561, 0.553, 0.533, 1)
INK = (0.945, 0.941, 0.925, 1)
SIGNAL = (0.949, 0.329, 0.176, 1)
WHITE = (1, 1, 1, 1)
SUB_PIE_LINE = (0.353, 0.349, 0.333, 1)
SUB_PIE_LIT = (0.290, 0.286, 0.275, 1)

# Blender's own interface font.
FONT = 0
LABEL_SIZE = 12
# From one line of a label to the next.
LINE_HEIGHT = 15


@dataclass(frozen=True)
class Line:
    """The line from the dial to the pointer, in shares of that way."""

    # Where it ends: 1 at the pointer, less while it flies into the dial.
    tip: float
    # The part in signal red; the rest is dashed.
    lit: tuple[float, float]
    # Where it meets the slot a click picks, or None where it meets none.
    contact: float | None


@dataclass(frozen=True)
class Look:
    """What decides how a pie is drawn. The pie being left keeps its last."""

    pie: model.Pie
    depth: int
    # In canvas units; None while the pointer is off the canvas.
    pointer: tuple[float, float] | None
    heading: float
    # 0 with the needle in the dial, 1 with the hover disc.
    hover: float
    # The sub-pie slot the pointer rests on and how far its fill has come.
    filling: tuple[int, float] | None
    # What labels() gave for the pie, and how far each long label has slid.
    labels: tuple[tuple[str, float, float], ...]
    slide: dict[int, float]
    # The slot the editor's menu acts on.
    selected: int | None
    # The slots that cannot run where the pie is open.
    disabled: frozenset[int] = frozenset()
    # The slot a click picks, and the line that shows it in an open pie.
    picked: int | None = None
    line: Line | None = None

    @property
    def dial(self):
        return layout.SUB_PIE_DIAL if self.depth > 1 else 1


class Canvas:
    """Turns canvas units into the pixels of a region."""

    def __init__(self, size, centre, scale):
        """size is the region's, centre the pie's in it, both in pixels."""
        self.size, self.centre, self.scale = size, centre, scale
        # What is drawn next is this opaque, and this size around origin.
        self.opacity = 1.0
        self.zoom = 1.0
        self.origin = (0.0, 0.0)

    def pixels(self, points, bearing=0):
        """Return the points in pixels, turned clockwise around the centre."""
        angle = math.radians(bearing)
        sin, cos = math.sin(angle), math.cos(angle)
        turned = [(x * cos + y * sin, y * cos - x * sin) for x, y in points]
        return [
            (
                self.centre[0]
                + (self.origin[0] + (x - self.origin[0]) * self.zoom) * self.scale,
                self.centre[1]
                + (self.origin[1] + (y - self.origin[1]) * self.zoom) * self.scale,
            )
            for x, y in turned
        ]

    def units(self, location):
        return (
            (location[0] - self.centre[0]) / self.scale,
            (location[1] - self.centre[1]) / self.scale,
        )

    def _colour(self, colour):
        return (*colour[:3], colour[3] * self.opacity)

    def fill(self, points, colour, bearing=0):
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.uniform_float("color", self._colour(colour))
        batch = batch_for_shader(
            shader, "TRI_FAN", {"pos": self.pixels(points, bearing)}
        )
        batch.draw(shader)

    def line(self, points, colour, width):
        shader = gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")
        shader.uniform_float("viewportSize", self.size)
        shader.uniform_float("lineWidth", width * self.scale * self.zoom)
        shader.uniform_float("color", self._colour(colour))
        batch_for_shader(shader, "LINE_STRIP", {"pos": self.pixels(points)}).draw(
            shader
        )

    def dashes(self, start, end, colour, width):
        """Draw a dashed line between two points."""
        length = math.dist(start, end)
        for n in range(math.ceil(length / (2 * layout.LINE_DASH))):
            ends = [
                tuple(a + (b - a) * min(1, at / length) for a, b in zip(start, end))
                for at in (2 * n * layout.LINE_DASH, (2 * n + 1) * layout.LINE_DASH)
            ]
            self.line(ends, colour, width)

    def text(self, text, x, y, size, colour):
        """Draw text centred on x with its baseline at y."""
        blf.size(FONT, size * self.zoom * self.scale)
        blf.color(FONT, *self._colour(colour))
        ((middle, bottom),) = self.pixels([(x, y)])
        blf.position(FONT, middle - blf.dimensions(FONT, text)[0] / 2, bottom, 0)
        blf.draw(FONT, text)
        # Drawing text turns blending off, and what fades needs it.
        gpu.state.blend_set("ALPHA")

    def label(self, text, span, y, colour, offset):
        """Draw a slot's label from the left of span, slid left by offset and
        cut at both ends of span."""
        left, right = span
        height = LABEL_SIZE * self.zoom * self.scale
        blf.size(FONT, height)
        blf.color(FONT, *self._colour(colour))
        (start, bottom), (low, _), (high, _) = self.pixels(
            [(left - offset, y), (left - 2, y), (right + 2, y)]
        )
        blf.enable(FONT, blf.CLIPPING)
        blf.clipping(FONT, low, bottom - height, high, bottom + 2 * height)
        blf.position(FONT, start, bottom, 0)
        blf.draw(FONT, text)
        blf.disable(FONT, blf.CLIPPING)
        gpu.state.blend_set("ALPHA")


def fitted(context, count):
    """Return the editor's canvas for a pie of count slots: centred in what
    the sidebar leaves of the region and as large as fits."""
    region = context.region
    # The sidebar lies over the right of the canvas.
    sidebar = next(r for r in context.area.regions if r.type == "UI")
    width = region.width - (sidebar.width if sidebar.width > 1 else 0)
    scale = context.preferences.system.ui_scale
    scale *= layout.fit(width / scale, region.height / scale, count)
    return Canvas((region.width, region.height), (width / 2, region.height / 2), scale)


def measure(text):
    blf.size(FONT, LABEL_SIZE)
    return blf.dimensions(FONT, text)[0]


def _lines(text, count):
    """Return the label as the lines it is drawn in: one, or in the square
    slot of a small pie as many as its words need."""
    if count > model.FEW_SLOTS:
        return [text]
    lines = [""]
    for word in text.split():
        joined = f"{lines[-1]} {word}".strip()
        if lines[-1] and measure(joined) > layout.SQUARE - 2 * layout.LABEL_PAD:
            lines.append(word)
        else:
            lines[-1] = joined
    return lines


def labels(shown):
    """Return the label, the width of its longest line and the slot's width
    for each slot."""
    count = len(shown.slots)
    result = []
    for content in shown.slots:
        text = "" if content is None else label(bpy.context, content).upper()
        width = max(measure(line) for line in _lines(text, count))
        result.append((text, width, layout.slot_width(width, count)))
    return tuple(result)


def _mix(a, b, amount):
    return tuple(x + (y - x) * amount for x, y in zip(a, b))


def _circle(radius):
    return [layout.point(radius, bearing) for bearing in range(0, 361, 5)]


def draw(canvas, look, opened):
    """Draw a pie that is opened by that share, 1 when it is fully open."""
    canvas.opacity *= opened
    _draw_dial(canvas, look, opened)
    pull = layout.OPEN_PULL + (1 - layout.OPEN_PULL) * opened
    if look.line is not None:
        _draw_line(canvas, look, False)
    for slot, content in enumerate(look.pie.slots):
        _draw_slot(canvas, look, slot, content, pull)
    if look.line is not None:
        _draw_line(canvas, look, True)
    canvas.opacity = 1.0


def _draw_line(canvas, look, contact):
    """Draw the line under the slots, or its contact point over them."""
    x, y = look.pointer
    far = math.hypot(x, y)
    start = (layout.DIAL_RADIUS * look.dial + layout.LINE_START) / far

    def at(share):
        along = start + (1 - start) * share
        return x * along, y * along

    line = look.line
    if contact:
        if line.contact is not None and line.contact <= line.tip:
            dot = [
                (at(line.contact)[0] + dx, at(line.contact)[1] + dy)
                for dx, dy in _circle(3.5)
            ]
            canvas.fill(dot, WHITE)
        return
    low, high = line.lit
    grey = (*STONE[:3], 0.7)
    canvas.dashes(at(0), at(low), grey, 1.5)
    if high > low:
        canvas.line([at(low), at(high)], SIGNAL, 1.5)
    canvas.dashes(at(high), at(line.tip), grey, 1.5)


def _draw_dial(canvas, look, opened):
    hover = layout.ease_in_out(look.hover)
    dial = layout.DIAL_RADIUS * look.dial
    ring = layout.RING_RADIUS * look.dial
    pull = layout.OPEN_PULL + (1 - layout.OPEN_PULL) * opened
    zoom, origin = canvas.zoom, canvas.origin
    if opened < 1:
        # The dial grows around its own centre, which a pie being left
        # never does.
        canvas.zoom, canvas.origin = (
            layout.OPEN_DIAL + (1 - layout.OPEN_DIAL) * opened,
            (0.0, 0.0),
        )
    count = len(look.pie.slots)
    lit = None
    if look.picked is not None:
        lit = layout.tick_at(layout.bearings(count)[look.picked])
    # Over a scene the dial needs a ground of its own, as the slots have.
    canvas.fill(_circle(ring), GROUND)
    canvas.line(_circle(ring), LINE, 1.5)
    for bearing, inner, outer, major in layout.ticks(dial, hover):
        on = bearing == lit
        colour = SIGNAL if on else INK if major else (*STONE[:3], 0.55)
        tick = [layout.point(inner, bearing), layout.point(outer, bearing)]
        canvas.line(tick, colour, 3 if on else 2 if major else 1)
    small = 1 - hover
    # The outer arrow slides onto the ring, shrinks and fades.
    middle = dial + 12 - 8 * hover
    arrow = [
        (0, middle + 4 * small),
        (5 * small, middle - 4 * small),
        (-5 * small, middle - 4 * small),
    ]
    canvas.fill(arrow, (*SIGNAL[:3], small), look.heading)
    # The needle fades out before the disc is full, and shrinks into the
    # centre while the disc grows out of it.
    fade = 1 - min(1.0, hover * 1.3)
    needle = (*SIGNAL[:3], fade)
    length, half = dial - layout.NEEDLE_INSET, dial * 0.15
    north = [(0, length * small), (half * small, 3 * small), (-half * small, 3 * small)]
    south = [
        (-half * small, -3 * small),
        (half * small, -3 * small),
        (0, -length * small),
    ]
    canvas.fill(north, needle, look.heading)
    canvas.fill(south, (*INK[:3], fade), look.heading)
    if hover > 0:
        disc = _circle(length * layout.HOVER_DISC * hover)
        canvas.fill(disc, SIGNAL)
        canvas.line(disc, WHITE, 3 * min(1.0, hover * 2))
    canvas.zoom, canvas.origin = zoom, origin
    below = "BACK" if look.depth > 1 else "CLOSE"
    colour = _mix((*STONE[:3], 0.6), INK, hover)
    _draw_tag(canvas, below, -(ring + 26) * pull, 11, colour)
    _draw_tag(canvas, look.pie.name.upper(), (ring + 14) * pull, 12, INK)


def _draw_tag(canvas, text, y, size, colour):
    """Draw text centred above or below the dial, on a ground of its own."""
    blf.size(FONT, size)
    half = blf.dimensions(FONT, text)[0] / 2 + 6
    box = [(-half, y - 5), (half, y - 5), (half, y + size + 2), (-half, y + size + 2)]
    canvas.fill(box, GROUND)
    canvas.text(text, 0, y, size, colour)


def _draw_slot(canvas, look, slot, content, pull):
    count = len(look.pie.slots)
    disabled = slot in look.disabled
    amount = float(slot == look.picked and not disabled)
    text, _, width = look.labels[slot]
    height = layout.slot_height(count)
    left, bottom = layout.slot_corner(slot, count, width, pull)
    right, top = left + width, bottom + height
    box = [(left, bottom), (right, bottom), (right, top), (left, top)]
    sub_pie = isinstance(content, model.SubPieSlot)
    fill = 0.0
    if look.filling is not None and look.filling[0] == slot:
        fill = look.filling[1]
    if sub_pie:
        canvas.fill(box, _mix(GROUND, SUB_PIE_LIT, amount))
        if fill > 0:
            x0, y0, x1, y1 = layout.filled(slot, count, fill)
            part = [
                (left + x0 * width, bottom + y0 * height),
                (left + x1 * width, bottom + y0 * height),
                (left + x1 * width, bottom + y1 * height),
                (left + x0 * width, bottom + y1 * height),
            ]
            canvas.fill(part, SIGNAL)
        outline = SIGNAL if fill > 0 else _mix(SUB_PIE_LINE, STONE, amount)
        canvas.line([*box, box[0]], outline, 1)
        marker = [(right - 9, top), (right, top), (right, top - 9)]
        canvas.fill(marker, WHITE if fill > 0.85 else SIGNAL)
    else:
        canvas.fill(box, _mix(GROUND, SIGNAL, amount))
        canvas.line([*box, box[0]], _mix(LINE, SIGNAL, amount), 1)
    if slot == look.selected:
        canvas.line([*box, box[0]], WHITE, 2)
    colour = WHITE if fill > 0 else _mix(INK, WHITE, amount)
    if disabled:
        colour = (*STONE[:3], 0.55)
    pad = layout.LABEL_PAD
    lines = _lines(text, count)
    for row, line in enumerate(lines):
        baseline = bottom + height / 2 - 4 + ((len(lines) - 1) / 2 - row) * LINE_HEIGHT
        if measure(line) > width - 2 * pad:
            offset = look.slide.get(slot, 0.0)
            canvas.label(line, (left + pad, right - pad), baseline, colour, offset)
        else:
            canvas.text(line, (left + right) / 2, baseline, LABEL_SIZE, colour)


def label(context, slot):
    if slot.label:
        return slot.label
    if isinstance(slot, model.ToolSlot):
        name = tools.label(context, slot.space_type, slot.tool)
        return name or slot.tool.rpartition(".")[2].replace("_", " ")
    if isinstance(slot, model.OperatorSlot):
        operator = pie.operator_type(slot.idname)
        return slot.idname if operator is None else operator.name
    return next(stored.name for stored in storage.pies if stored.id == slot.pie)
