# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""How a pie on show moves.

A stage follows the pointer and decides how far each animation has come.
The editor's canvas keeps one and so does a pie open in an editor.
"""

import math
import time
from dataclasses import dataclass, field

import bpy

from ..core import layout, model
from . import paint

# Seconds between two frames of an animation.
FRAME = 1 / 60


def share(since, now):
    """Return how much of an animation that began at since is done, 0 to 1."""
    if bpy.context.preferences.view.use_reduce_motion:
        return 1.0
    return min(1.0, (now - since) / layout.MOTION)


def _widths(shown):
    return [width for _, _, width in paint.labels(shown)]


@dataclass
class Stage:
    # In canvas units from the pie's centre.
    pointer: tuple[float, float] = (0.0, 0.0)
    # The needle's bearing. A pointer at rest on the centre keeps the last.
    heading: float = 0.0
    # The centre's hover state runs from hover_from to hover_target.
    hover_from: float = 0.0
    hover_target: float = 0.0
    hover_since: float = 0.0
    # The sub-pie slot the pointer rests on, and since when.
    rest: tuple[int, float] | None = None
    # The slot under the pointer when the pie came on show. It does not open
    # until the pointer has left it.
    held: int | None = None
    opened: float = 0.0
    # The slot the pointer selects, and since when.
    selected: int | None = None
    selected_since: float = 0.0
    # How far each label that is too long for its slot has slid.
    slide: dict[int, float] = field(default_factory=dict)
    drawn: float = 0.0
    look: paint.Look | None = None
    # The slots that cannot run where the pie is open.
    disabled: frozenset[int] = frozenset()
    # Whether a line from the dial to the pointer shows what a click picks.
    # How much of it is out of the dial and how much of it is lit, 0 to 1,
    # where it met the last slot it picked and whether it has let go.
    line: bool = False
    out: float = 1.0
    lit: float = 0.0
    contact: float = 1.0
    gone: bool = False
    # Where the last pie was drawn, in pixels.
    centre: tuple[float, float] = (0.0, 0.0)
    # The pie being left, where it was drawn, what it shrinks to and around
    # which of its points.
    ghost: paint.Look | None = None
    ghost_centre: tuple[float, float] = (0.0, 0.0)
    shrink: float = 1.0
    origin: tuple[float, float] = (0.0, 0.0)

    def follow(self, pointer, shown, opening):
        """Record where the pointer is. Return whether it moved.

        opening is whether resting on a sub-pie slot opens it.
        """
        if pointer == self.pointer:
            return False
        self.pointer = pointer
        if math.hypot(*pointer) >= layout.NEEDLE_REST:
            self.heading = layout.bearing_to(*pointer)
        under = None if shown is None else layout.slot_under(*pointer, _widths(shown))
        if under != self.held:
            self.held = None
        opens = (
            opening
            and under is not None
            and under != self.held
            and isinstance(shown.slots[under], model.SubPieSlot)
        )
        if not opens:
            self.rest = None
        elif self.rest is None or self.rest[0] != under:
            self.rest = under, time.perf_counter()
        return True

    def due(self):
        """Return the sub-pie slot the pointer has rested on long enough, once."""
        if self.rest is None:
            return None
        slot, since = self.rest
        if time.perf_counter() - since < layout.HOVER_DELAY:
            return None
        self.rest = None
        return slot

    def _hover(self, inside, now):
        """Return how far the centre is into its hover state, 0 to 1."""
        step = share(self.hover_since, now)
        hover = layout.toward(self.hover_from, self.hover_target, step)
        if inside != self.hover_target:
            # It turns around from wherever it is.
            self.hover_from, self.hover_target = hover, float(inside)
            self.hover_since = now
        return hover

    def _arrive(self, canvas, shown, depth, now):
        """Start the opening of a pie that was not on show at the last draw."""
        before = self.look
        if before is not None and (before.pie.id, before.depth) == (shown.id, depth):
            return
        self.opened = now
        self.rest = None
        self.held = layout.slot_under(*self.pointer, _widths(shown))
        # The pie being left keeps the old one.
        self.slide = {}
        self.ghost = None
        if before is None or abs(depth - before.depth) != 1:
            return
        self.ghost, self.ghost_centre = before, self.centre
        if depth < before.depth:
            self.shrink, self.origin = layout.SUB_PIE_SHRINK, (0.0, 0.0)
            return
        # A pie that is left for its sub-pie shrinks around the pointer.
        self.shrink = layout.PARENT_SHRINK
        self.origin = tuple(
            self.pointer[axis]
            + (canvas.centre[axis] - self.centre[axis]) / canvas.scale
            for axis in (0, 1)
        )

    def _line(self, picked, widths, start, step):
        """Move the line by step seconds. Return it, or None with the pointer
        on the dial, and whether it is not at rest."""
        far = math.hypot(*self.pointer)
        if far <= start:
            return None, False
        gone = picked is None and far > layout.LINE_REACH
        touch = None if picked is None else layout.enters(*self.pointer, picked, widths)
        if touch is not None:
            touch = min(1.0, max(0.0, (touch * far - start) / (far - start)))
        if picked is not None:
            self.contact = 1.0 if touch is None else touch
        if self.gone and not gone:
            # It comes back in the colour it has there.
            self.lit = float(picked is not None)
        self.gone = gone
        # A line that let go keeps its colour on the way in.
        glow = self.lit if gone else float(picked is not None)
        if bpy.context.preferences.view.use_reduce_motion:
            self.out, self.lit = float(not gone), glow
        else:
            leave = layout.LINE_LEAVE if gone else layout.LINE_RETURN
            self.out = layout.toward(self.out, float(not gone), step / leave)
            self.lit = layout.toward(self.lit, glow, step / layout.MOTION)
        tip = 1 - layout.pulled(1 - self.out)
        grown = layout.ease_out(self.lit)
        low = min(tip, self.contact * (1 - grown))
        high = min(tip, self.contact + (1 - self.contact) * grown)
        line = paint.Line(tip, (low, high), touch)
        return line, self.out != float(not gone) or self.lit != glow

    def _slide(self, labels, selected, now, step):
        """Move the labels that are too long. Return whether one is not at rest."""
        if selected != self.selected:
            self.selected, self.selected_since = selected, now
        sliding = False
        for slot, (_, text_width, width) in enumerate(labels):
            over = text_width - (width - 2 * layout.LABEL_PAD)
            if over <= 0:
                continue
            held = now - self.selected_since if slot == selected else None
            if bpy.context.preferences.view.use_reduce_motion:
                waited = held is not None and held > layout.LABEL_WAIT
                offset = over if waited else 0.0
            else:
                offset = layout.slide(self.slide.get(slot, 0.0), over, held, step)
            self.slide[slot] = offset
            sliding = sliding or (offset < over if slot == selected else offset > 0)
        return sliding

    def paint(self, canvas, shown, depth, on, selected=None):
        """Draw the pie, and the one being left while it fades. Return
        whether another frame is due.

        on is whether the pointer is over the pie's canvas; selected is the
        slot the editor outlines.
        """
        now = time.perf_counter()
        self._arrive(canvas, shown, depth, now)
        self.centre = canvas.centre
        pointer = self.pointer if on else None
        ring = layout.RING_RADIUS * (layout.SUB_PIE_DIAL if depth > 1 else 1)
        inside = on and math.hypot(*self.pointer) <= ring
        if self.opened == now:
            # A pie that opens under the pointer shows the disc at once, not
            # the needle on its way to it.
            self.hover_from = self.hover_target = float(inside)
        hover = self._hover(inside, now)
        filling = None
        if self.rest is not None:
            slot, since = self.rest
            filling = slot, min(1.0, (now - since) / layout.HOVER_DELAY)
        labels = paint.labels(shown)
        widths = [width for _, _, width in labels]
        picked = None
        if pointer is not None and not inside:
            picked = layout.slot_picked(*pointer, widths)
        # A draw after a long rest is not a long step.
        step = min(0.05, now - self.drawn)
        self.drawn = now
        sliding = self._slide(labels, picked, now, step)
        line = None
        if self.line and pointer is not None:
            start = layout.DIAL_RADIUS * ring / layout.RING_RADIUS + layout.LINE_START
            line, flying = self._line(picked, widths, start, step)
            sliding = sliding or flying
        look = paint.Look(
            shown,
            depth,
            pointer,
            self.heading,
            hover,
            filling,
            labels,
            dict(self.slide),
            selected,
            self.disabled,
            picked,
            line,
        )
        opened = share(self.opened, now)
        if self.ghost is not None and opened < 1:
            left = layout.ease_out(1 - opened)
            canvas.centre = self.ghost_centre
            canvas.opacity = left
            canvas.zoom = self.shrink + (1 - self.shrink) * left
            canvas.origin = self.origin
            paint.draw(canvas, self.ghost, 1.0)
            canvas.centre = self.centre
            canvas.zoom, canvas.origin = 1.0, (0.0, 0.0)
        paint.draw(canvas, look, layout.ease_out(opened))
        self.look = look
        moving = opened < 1 or hover != self.hover_target or self.rest is not None
        return moving or sliding
