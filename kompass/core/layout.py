# SPDX-License-Identifier: GPL-3.0-or-later
"""Where the parts of a pie sit on the editor canvas, and how they move.

Lengths are pixels at UI scale 1, measured from the centre of the pie with
x to the right and y up. Bearings are degrees clockwise from north. Times
are seconds. The numbers are those of variant G in
docs/design/pie-playground.html and of docs/design/pie-motion.html.
"""

import math

from .model import SLOT_DIRECTIONS

PIE_RADIUS = 150
# A slot grows from SLOT_WIDTH to fit its label, up to SLOT_MAX_WIDTH.
SLOT_WIDTH = 120
SLOT_MAX_WIDTH = 180
SLOT_HEIGHT = 32
# The room between a slot's side and its label.
LABEL_PAD = 12
# The tips of the dial's ticks, and the ring drawn around them.
DIAL_RADIUS = 52
RING_RADIUS = 55
SUB_PIE_DIAL = 0.72
# Closer to the centre than this, the needle keeps its heading.
NEEDLE_REST = 8
# The needle's tip is this far inside the tips of the ticks.
NEEDLE_INSET = 22
# The radius of the centre's hover disc, as a share of the needle's length.
HOVER_DISC = 0.75
TICK = 5
MAJOR_TICK = 12

# A label too long for its slot waits this long on the selected slot, slides
# left at this speed and eases back with this time constant.
LABEL_WAIT = 0.4
LABEL_SPEED = 40
LABEL_RETURN = 0.06

# How long every animation takes.
MOTION = 0.12
# How long the pointer rests on a sub-pie slot before the sub-pie opens.
HOVER_DELAY = 0.1
# A pie opens with its slots at this share of their distance from the centre
# and its dial at this share of its size.
OPEN_PULL = 0.88
OPEN_DIAL = 0.92
# What a pie shrinks to while its sub-pie opens, and a sub-pie on the way back.
PARENT_SHRINK = 0.9
SUB_PIE_SHRINK = 0.88

# Half the width and height the whole pie needs, with a margin.
_HALF_WIDTH = PIE_RADIUS + SLOT_MAX_WIDTH + 12
_HALF_HEIGHT = PIE_RADIUS + SLOT_HEIGHT * 1.5 + 12

_BEARINGS = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SW": 225, "W": 270}
_BEARINGS["NW"] = 315
BEARINGS = tuple(_BEARINGS[direction] for direction in SLOT_DIRECTIONS)


def fit(width, height):
    """Return the factor, at most 1, that fits the pie into that many units."""
    return min(1, width / (2 * _HALF_WIDTH), height / (2 * _HALF_HEIGHT))


def point(radius, bearing):
    angle = math.radians(bearing)
    return math.sin(angle) * radius, math.cos(angle) * radius


def slot_width(label):
    """Return the width of a slot whose label is that wide."""
    return min(SLOT_MAX_WIDTH, max(SLOT_WIDTH, math.ceil(label) + 2 * LABEL_PAD))


def slot_corner(slot, width=SLOT_WIDTH, pull=1.0):
    """Return the left and bottom of slot n, which is SLOT_DIRECTIONS[n].

    pull is the share of its distance from the centre the slot has reached
    while the pie opens.
    """
    bearing = BEARINGS[slot]
    x, y = point(PIE_RADIUS * pull, bearing)
    left = x - width / 2
    if bearing in {90, 270}:
        # East and west start at the pie's radius instead of straddling it.
        left += math.copysign(width / 2 - 4, x)
    elif bearing % 90:
        # The diagonal slots move outwards to clear the ones above and below.
        left += math.copysign(SLOT_WIDTH * 0.2, x)
    bottom = y - SLOT_HEIGHT / 2
    if bearing in {0, 180}:
        bottom += math.copysign(SLOT_HEIGHT / 2, y)
    return left, bottom


def slot_under(x, y, widths):
    """Return the slot whose box the pointer is on, or None.

    widths is the width of each slot.
    """
    for slot, width in enumerate(widths):
        left, bottom = slot_corner(slot, width)
        if left < x < left + width and bottom < y < bottom + SLOT_HEIGHT:
            return slot
    return None


def slide(offset, over, selected, step):
    """Return how far a label that is over too long has slid, step later.

    selected is how long its slot has been the selected one, or None.
    """
    if selected is None:
        return 0.0 if offset < 0.3 else offset * math.exp(-step / LABEL_RETURN)
    if selected > LABEL_WAIT:
        return min(over, offset + LABEL_SPEED * step)
    return offset


def filled(slot, amount):
    """Return the part of a sub-pie slot that is filled, as shares of its box.

    The result is left, bottom, right, top, each from 0 to 1. The fill grows
    away from the centre: north upward, south downward, the others sideways.
    """
    bearing = BEARINGS[slot]
    if bearing == 0:
        return 0.0, 0.0, 1.0, amount
    if bearing == 180:
        return 0.0, 1 - amount, 1.0, 1.0
    if bearing > 180:
        return 1 - amount, 0.0, 1.0, 1.0
    return 0.0, 0.0, amount, 1.0


def bearing_to(x, y):
    return math.degrees(math.atan2(x, y)) % 360


def slot_at(x, y, ring=RING_RADIUS):
    """Return the slot the pointer selects, or None inside the dial's ring."""
    if math.hypot(x, y) <= ring:
        return None
    heading = bearing_to(x, y)
    return min(range(len(BEARINGS)), key=lambda slot: _apart(heading, BEARINGS[slot]))


def highlight(x, y, slot, ring=RING_RADIUS):
    """Return how strongly slot is lit, 0 to 1, for a pointer at x, y.

    It rises with the distance past the ring and with how close the pointer's
    bearing is to the slot's. The selected slot keeps at least 0.3.
    """
    distance = math.hypot(x, y)
    if distance <= ring:
        return 0.0
    reach = max(20, (PIE_RADIUS - ring) * 0.6)
    radial = min(1.0, (distance - ring) / reach)
    near = max(0.0, 1 - _apart(bearing_to(x, y), BEARINGS[slot]) / 45)
    if slot_at(x, y, ring) == slot:
        return max(0.3, near * near * radial)
    return near * near * radial * 0.55


def ticks(radius=DIAL_RADIUS, hover=0.0):
    """Return (bearing, inner radius, outer radius, is major) for each tick.

    hover, 0 to 1, shortens the major ticks to the length of the others.
    """
    major = MAJOR_TICK + (TICK - MAJOR_TICK) * hover
    return [
        (
            bearing,
            radius - (major if bearing % 45 == 0 else TICK),
            radius,
            bearing % 45 == 0,
        )
        for bearing in range(0, 360, 5)
    ]


def ease_out(share):
    return 1 - (1 - share) ** 3


def ease_in_out(share):
    if share < 0.5:
        return 4 * share**3
    return 1 - (-2 * share + 2) ** 3 / 2


def toward(value, target, step):
    """Return value moved by at most step in the direction of target."""
    if value < target:
        return min(target, value + step)
    return max(target, value - step)


def _apart(a, b):
    return abs((a - b + 180) % 360 - 180)
