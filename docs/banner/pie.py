# SPDX-License-Identifier: GPL-3.0-or-later
"""A pie as the canvas keeps it, following the pointer frame by frame."""

import math

from glyphs import FONT
from tracks import ANGLE, COLOUR, POSITION, SHARE, put

GROUND = "#0e0e0e"
LINE = "#2c2c2c"
INK = "#f1f0ec"
STONE = "#8f8d88"
SIGNAL = "#f2542d"
WHITE = "#ffffff"
SUB_LINE = "#5a5955"
SUB_HOT = "#4a4946"

# Sizes from kompass/core/layout.py.
RING = 150
SLOT_HEIGHT = 72
SLOT_WIDTH = 120
SLOT_MAX_WIDTH = 180
LABEL_PAD = 12
DIAL = 52
RING_RADIUS = 55
NEEDLE_INSET = 22
HOVER_DISC = 0.75
LINE_START = 22
MOTION = 0.12
HOVER_DELAY = 0.1
NEEDLE_EASE = 0.045
LABEL_SIZE = 14

ROOT_CENTRE = (600, 300)


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    return 4 * t**3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def clamp(x):
    return max(0.0, min(1.0, x))


def lerp(a, b, t):
    return a + (b - a) * t


def mix(a, b, t):
    return tuple(lerp(x, y, t) for x, y in zip(rgb(a), rgb(b)))


def rgb(colour):
    if isinstance(colour, tuple):
        return colour
    return tuple(int(colour[i : i + 2], 16) for i in (1, 3, 5))


class Pie:
    """A pie's state as the canvas keeps it."""

    def __init__(self, key, spec, dial_share):
        self.key = key
        self.name, items = spec
        self.k = dial_share
        self.dial = DIAL * dial_share
        self.inner = RING_RADIUS * dial_share
        self.slots = []
        for label, bearing, sub in items:
            width = FONT.width(label.upper(), LABEL_SIZE, 0.08)
            self.slots.append(
                {
                    "label": label.upper(),
                    "bearing": bearing,
                    "sub": sub,
                    "w": min(
                        SLOT_MAX_WIDTH,
                        max(SLOT_WIDTH, math.ceil(width) + 2 * LABEL_PAD),
                    ),
                }
            )
        self.centre = ROOT_CENTRE
        self.mode = "hidden"
        self.open_share = 0.0
        self.ghost = (ROOT_CENTRE, 1.0, 1.0)
        self.ghost_share = 0.0
        self.reset()

    def reset(self):
        self.angle = 0.0
        self.hover = 0.0
        self.amounts = [0.0] * len(self.slots)
        self.fills = [0.0] * len(self.slots)
        self.red_slot = None
        self.red = 0.0
        self.contact = self.centre
        self.suppress = None

    def open(self, centre, pointer):
        self.centre = centre
        self.mode = "open"
        self.open_share = 0.0
        self.reset()
        self.hover = 1.0 if math.dist(pointer, centre) <= self.inner else 0.0

    def to_ghost(self, origin, shrink):
        self.mode = "ghost"
        self.ghost = (origin, shrink)
        self.ghost_share = 0.0

    def box(self, i, pull=1.0):
        """Return the slot's left, top, width and height."""
        slot = self.slots[i]
        sn, cs = (
            math.sin(math.radians(slot["bearing"])),
            math.cos(math.radians(slot["bearing"])),
        )
        w, h = slot["w"], SLOT_HEIGHT
        px, py = self.centre[0] + sn * RING * pull, self.centre[1] - cs * RING * pull
        return px - w / 2 + sn * w / 2, py - h / 2 - cs * h / 2, w, h

    def inside(self, i, p):
        x, y, w, h = self.box(i)
        return x <= p[0] <= x + w and y <= p[1] <= y + h

    def line_start(self, p):
        d = math.dist(p, self.centre)
        ux, uy = (p[0] - self.centre[0]) / d, (p[1] - self.centre[1]) / d
        r = self.dial + LINE_START
        return self.centre[0] + ux * r, self.centre[1] + uy * r

    def entry(self, i, a, b):
        """Return where the segment a-b enters the slot, as a share of it."""
        x, y, w, h = self.box(i)
        lo, hi = 0.0, 1.0
        for start, delta, low, high in (
            (a[0], b[0] - a[0], x, x + w),
            (a[1], b[1] - a[1], y, y + h),
        ):
            if delta == 0:
                if not low <= start <= high:
                    return None
                continue
            t1, t2 = (low - start) / delta, (high - start) / delta
            lo, hi = max(lo, min(t1, t2)), min(hi, max(t1, t2))
        return lo if lo <= hi else None

    def pick(self, p):
        """Return the picked slot and where the line meets it."""
        d = math.dist(p, self.centre)
        if d <= self.dial + LINE_START:
            return None, None
        a = self.line_start(p)
        best = None
        for i, _ in enumerate(self.slots):
            t = self.entry(i, a, p)
            if t is not None and (best is None or t < best[1] or self.inside(i, p)):
                best = (i, t)
                if self.inside(i, p):
                    break
        if best is None:
            return None, None
        t = best[1]
        return best[0], (lerp(a[0], p[0], t), lerp(a[1], p[1], t))

    def step(self, p, dt):
        """Follow the pointer for one frame; return True when a sub-pie opens."""
        d = math.dist(p, self.centre)
        if d > 8:
            target = math.degrees(
                math.atan2(p[0] - self.centre[0], self.centre[1] - p[1])
            )
            diff = (target - self.angle + 540) % 360 - 180
            self.angle += diff * (1 - math.exp(-dt / NEEDLE_EASE))
        towards = 1.0 if d <= self.inner else 0.0
        self.hover += max(-dt / MOTION, min(dt / MOTION, towards - self.hover))

        picked, contact = self.pick(p)
        for i, amount in enumerate(self.amounts):
            goal = 1.0 if i == picked else 0.0
            self.amounts[i] += max(-dt / MOTION, min(dt / MOTION, goal - amount))
        if picked is not None:
            if picked != self.red_slot:
                self.red_slot, self.red = picked, 0.0
            self.red = min(1.0, self.red + dt / MOTION)
            self.contact = contact
        else:
            self.red = max(0.0, self.red - dt / MOTION)

        opened = False
        for i, slot in enumerate(self.slots):
            here = self.inside(i, p)
            if self.suppress == i and not here:
                self.suppress = None
            if slot["sub"] and here and self.suppress != i:
                self.fills[i] = min(1.0, self.fills[i] + dt / HOVER_DELAY)
                opened = opened or self.fills[i] >= 1.0
            else:
                self.fills[i] = 0.0
        return opened

    def advance(self, dt):
        if self.mode == "open":
            self.open_share = min(1.0, self.open_share + dt / MOTION)
        elif self.mode == "closing":
            self.open_share = max(0.0, self.open_share - dt / MOTION)
            if self.open_share == 0:
                self.mode = "hidden"
        elif self.mode == "ghost":
            self.ghost_share = min(1.0, self.ghost_share + dt / MOTION)
            if self.ghost_share == 1:
                self.mode = "hidden"

    def record(self):
        k = self.key
        eo = ease_out(self.open_share) if self.mode in ("open", "closing") else 1.0
        if self.mode == "ghost":
            g = ease_out(self.ghost_share)
            origin, shrink = self.ghost
            s, fade = lerp(1, shrink, g), 1 - g
        else:
            origin, s, fade = self.centre, 1.0, 1.0
        opacity = 0.0 if self.mode == "hidden" else eo * fade
        pull = lerp(0.88, 1, eo)

        def at(q):
            return (
                origin[0] + s * (q[0] - origin[0]),
                origin[1] + s * (q[1] - origin[1]),
            )

        cx, cy = self.centre
        e = ease_in_out(clamp(self.hover))
        put(f"{k}-op", opacity, SHARE)
        put(f"{k}-dial-at", at(self.centre), POSITION)
        put(f"{k}-dial-s", s * lerp(0.92, 1, eo), SHARE / 4)
        put(f"{k}-angle", self.angle, ANGLE)
        put(f"{k}-needle-s", max(0.001, 1 - e), SHARE / 4)
        put(f"{k}-needle-op", 1 - clamp(e * 1.3), SHARE)
        put(f"{k}-disc-r", self.dial_disc() * e, POSITION / 2)
        put(f"{k}-disc-w", 3 * clamp(e * 2), SHARE * 5)
        put(f"{k}-arrow-at", (0, -lerp(self.dial + 12, self.dial + 4, e)), POSITION)
        put(f"{k}-arrow-s", max(0.001, 1 - e), SHARE / 4)
        put(f"{k}-arrow-op", 1 - e, SHARE)
        put(f"{k}-major-r", self.dial - lerp(12, 5, e) / 2, POSITION / 2)
        put(f"{k}-major-w", lerp(12, 5, e), POSITION / 2)
        put(f"{k}-title-at", at((cx, cy - (self.inner + 18) * pull)), POSITION)
        put(f"{k}-hint-at", at((cx, cy + (self.inner + 26) * pull)), POSITION)
        put(f"{k}-hint-fill", mix(STONE, INK, e), COLOUR)
        put(f"{k}-hint-op", lerp(0.6, 1, e), SHARE)
        put(f"{k}-s", s, SHARE / 4)
        for i, slot in enumerate(self.slots):
            x, y, w, h = self.box(i, pull)
            a = ease_in_out(clamp(self.amounts[i]))
            put(f"{k}-slot{i}-at", at((x + w / 2, y + h / 2)), POSITION)
            put(f"{k}-tick{i}-op", a, SHARE)
            wiped = slot["sub"] and self.fills[i] > 0
            put(
                f"{k}-slot{i}-text", rgb(WHITE) if wiped else mix(INK, WHITE, a), COLOUR
            )
            if slot["sub"]:
                f = self.fills[i]
                put(f"{k}-slot{i}-fill", mix(GROUND, SUB_HOT, a), COLOUR)
                put(f"{k}-slot{i}-stroke", mix(SUB_LINE, STONE, a), COLOUR)
                put(f"{k}-slot{i}-wipe", w * f, POSITION)
                put(f"{k}-slot{i}-wipe-x", w / 2 - w * f, POSITION)
                put(f"{k}-slot{i}-edge", 1.0 if f > 0 else 0.0, SHARE)
                put(
                    f"{k}-slot{i}-mark", rgb(WHITE) if f > 0.85 else rgb(SIGNAL), COLOUR
                )
            else:
                put(f"{k}-slot{i}-fill", mix(GROUND, SIGNAL, a), COLOUR)
                put(f"{k}-slot{i}-stroke", mix(LINE, SIGNAL, a), COLOUR)

    def dial_disc(self):
        return (self.dial - NEEDLE_INSET) * HOVER_DISC
