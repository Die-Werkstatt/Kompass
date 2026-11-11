# SPDX-License-Identifier: GPL-3.0-or-later
"""Where the parts of a pie sit on the editor canvas.

Lengths are pixels at UI scale 1, measured from the centre of the pie with
x to the right and y up. Bearings are degrees clockwise from north. The
numbers are those of variant G in docs/design/pie-playground.html.
"""

import math

from .model import SLOT_DIRECTIONS

PIE_RADIUS = 150
SLOT_WIDTH = 120
SLOT_HEIGHT = 32
# The tips of the dial's ticks, and the ring drawn around them.
DIAL_RADIUS = 52
RING_RADIUS = 55
SUB_PIE_DIAL = 0.72
# Closer to the centre than this, the needle keeps its heading.
NEEDLE_REST = 8

# Half the width and height the whole pie needs, with a margin.
_HALF_WIDTH = PIE_RADIUS + SLOT_WIDTH + 12
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


def slot_corner(slot):
    """Return the left and bottom of slot n, which is SLOT_DIRECTIONS[n]."""
    bearing = BEARINGS[slot]
    x, y = point(PIE_RADIUS, bearing)
    left = x - SLOT_WIDTH / 2
    if bearing in {90, 270}:
        # East and west start at the pie's radius instead of straddling it.
        left += math.copysign(SLOT_WIDTH / 2 - 4, x)
    elif bearing % 90:
        # The diagonal slots move outwards to clear the ones above and below.
        left += math.copysign(SLOT_WIDTH * 0.2, x)
    bottom = y - SLOT_HEIGHT / 2
    if bearing in {0, 180}:
        bottom += math.copysign(SLOT_HEIGHT / 2, y)
    return left, bottom


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


def ticks(radius=DIAL_RADIUS):
    """Return (bearing, inner radius, outer radius, is major) for each tick."""
    return [
        (bearing, radius - (12 if bearing % 45 == 0 else 5), radius, bearing % 45 == 0)
        for bearing in range(0, 360, 5)
    ]


def _apart(a, b):
    return abs((a - b + 180) % 360 - 180)
