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


def _share(since, now):
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
        step = _share(self.hover_since, now)
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

    def _slide(self, labels, pointer, now):
        """Move the labels that are too long. Return whether one is not at rest."""
        selected = None
        if pointer is not None:
            widths = [width for _, _, width in labels]
            selected = layout.slot_clicked(*pointer, widths)
        if selected != self.selected:
            self.selected, self.selected_since = selected, now
        # A draw after a long rest is not a long step.
        step = min(0.05, now - self.drawn)
        self.drawn = now
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
        hover = self._hover(on and math.hypot(*self.pointer) <= ring, now)
        filling = None
        if self.rest is not None:
            slot, since = self.rest
            filling = slot, min(1.0, (now - since) / layout.HOVER_DELAY)
        labels = paint.labels(shown)
        sliding = self._slide(labels, pointer, now)
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
        )
        opened = _share(self.opened, now)
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
