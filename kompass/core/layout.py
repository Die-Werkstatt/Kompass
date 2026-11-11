# SPDX-License-Identifier: GPL-3.0-or-later
"""Where the parts of a pie sit on the editor canvas, and how they move.

Lengths are pixels at UI scale 1, measured from the centre of the pie with
x to the right and y up. Bearings are degrees clockwise from north. Times
are seconds. The numbers are those of variant G in
docs/design/pie-playground.html and of docs/design/pie-motion.html.
"""

import math

from .model import NATIVE_SLOTS, SLOT_DIRECTIONS

PIE_RADIUS = 150
# The radius of a pie of 12 slots, and their bearings. With these every two
# neighbours of SLOT_WIDTH are 37 apart; at equal angles the slots near
# north and south would nearly touch.
WIDE_RADIUS = 170
WIDE_BEARINGS = (0, 42, 68, 90, 112, 138, 180, 222, 248, 270, 292, 318)
# A slot grows from SLOT_WIDTH to fit its label, up to SLOT_MAX_WIDTH.
SLOT_WIDTH = 120
SLOT_MAX_WIDTH = 180
SLOT_HEIGHT = 32
# A click this close to a slot counts for it.
CLICK_REACH = 24
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

_BEARINGS = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SW": 225, "W": 270}
_BEARINGS["NW"] = 315
BEARINGS = tuple(_BEARINGS[direction] for direction in SLOT_DIRECTIONS)


def bearings(count):
    """Return the bearing of each slot of a pie of that many slots."""
    return BEARINGS if count == NATIVE_SLOTS else WIDE_BEARINGS


def radius(count):
    return PIE_RADIUS if count == NATIVE_SLOTS else WIDE_RADIUS


def fit(width, height, count):
    """Return the factor, at most 1, that fits the pie into that many units."""
    # Half of what the whole pie needs, with a margin.
    half_width = radius(count) + SLOT_MAX_WIDTH + 12
    half_height = radius(count) + SLOT_HEIGHT * 1.5 + 12
    return min(1, width / (2 * half_width), height / (2 * half_height))


def point(distance, bearing):
    angle = math.radians(bearing)
    return math.sin(angle) * distance, math.cos(angle) * distance


def slot_width(label):
    """Return the width of a slot whose label is that wide."""
    return min(SLOT_MAX_WIDTH, max(SLOT_WIDTH, math.ceil(label) + 2 * LABEL_PAD))


def slot_corner(slot, count, width=SLOT_WIDTH, pull=1.0):
    """Return the left and bottom of slot n of a pie of count slots.

    The slot sits on the pie's ring at its bearing and moves out by half its
    width times the bearing's sine and half its height times its cosine:
    east and west start at the ring, north and south lie beyond it. pull is
    the share of its distance from the centre the slot has reached while the
    pie opens.
    """
    bearing = bearings(count)[slot]
    x, y = point(radius(count) * pull, bearing)
    out_x, out_y = point(1, bearing)
    left = x - width / 2 + out_x * width / 2
    bottom = y - SLOT_HEIGHT / 2 + out_y * SLOT_HEIGHT / 2
    return left, bottom


def slot_under(x, y, widths):
    """Return the slot whose box the pointer is on, or None.

    widths is the width of each slot.
    """
    for slot, width in enumerate(widths):
        left, bottom = slot_corner(slot, len(widths), width)
        if left < x < left + width and bottom < y < bottom + SLOT_HEIGHT:
            return slot
    return None


def _gap(x, y, slot, count, width):
    """Return how far x, y is from the box of slot, 0 on it."""
    left, bottom = slot_corner(slot, count, width)
    return math.hypot(
        max(left - x, 0, x - left - width),
        max(bottom - y, 0, y - bottom - SLOT_HEIGHT),
    )


def slot_clicked(x, y, widths):
    """Return the slot nearest to a click, or None beyond CLICK_REACH of all."""
    nearest, reach = None, CLICK_REACH
    for slot, width in enumerate(widths):
        distance = _gap(x, y, slot, len(widths), width)
        if distance <= reach:
            nearest, reach = slot, distance
    return nearest


def slide(offset, over, selected, step):
    """Return how far a label that is over too long has slid, step later.

    selected is how long its slot has been the selected one, or None.
    """
    if selected is None:
        return 0.0 if offset < 0.3 else offset * math.exp(-step / LABEL_RETURN)
    if selected > LABEL_WAIT:
        return min(over, offset + LABEL_SPEED * step)
    return offset


def filled(slot, count, amount):
    """Return the part of a sub-pie slot that is filled, as shares of its box.

    The result is left, bottom, right, top, each from 0 to 1. The fill grows
    away from the centre along the stronger axis of the slot's bearing.
    """
    x, y = point(1, bearings(count)[slot])
    if abs(y) > abs(x) + 1e-9:
        return (0.0, 0.0, 1.0, amount) if y > 0 else (0.0, 1 - amount, 1.0, 1.0)
    return (0.0, 0.0, amount, 1.0) if x > 0 else (1 - amount, 0.0, 1.0, 1.0)


def bearing_to(x, y):
    return math.degrees(math.atan2(x, y)) % 360


def slot_at(x, y, count, ring=RING_RADIUS):
    """Return the slot the pointer selects, or None inside the dial's ring."""
    if math.hypot(x, y) <= ring:
        return None
    heading = bearing_to(x, y)
    return min(range(count), key=lambda slot: _apart(heading, bearings(count)[slot]))


def highlight(x, y, slot, widths, ring=RING_RADIUS):
    """Return how strongly slot is lit, 0 to 1, for a pointer at x, y.

    It rises with the distance past the ring and with how close the pointer's
    bearing is to the slot's. The selected slot keeps at least 0.3. Off the
    slot's box all of it fades, to nothing at CLICK_REACH, where a click stops
    counting for the slot.
    """
    count = len(widths)
    distance = math.hypot(x, y)
    close = 1 - _gap(x, y, slot, count, widths[slot]) / CLICK_REACH
    if distance <= ring or close <= 0:
        return 0.0
    reach = max(20, (radius(count) - ring) * 0.6)
    radial = min(1.0, (distance - ring) / reach)
    apart = _apart(bearing_to(x, y), bearings(count)[slot])
    near = max(0.0, 1 - apart / (360 / count))
    if slot_at(x, y, count, ring) == slot:
        return max(0.3, near * near * radial) * close
    return near * near * radial * 0.55 * close


def ticks(dial=DIAL_RADIUS, hover=0.0):
    """Return (bearing, inner radius, outer radius, is major) for each tick.

    hover, 0 to 1, shortens the major ticks to the length of the others.
    """
    major = MAJOR_TICK + (TICK - MAJOR_TICK) * hover
    return [
        (
            bearing,
            dial - (major if bearing % 45 == 0 else TICK),
            dial,
            bearing % 45 == 0,
        )
        for bearing in range(0, 360, 5)
    ]


def tick_at(bearing):
    """Return the bearing of the tick nearest to that bearing."""
    return round(bearing / 5) * 5 % 360


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
