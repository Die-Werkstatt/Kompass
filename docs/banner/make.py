#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Write kompass-banner.svg, the looping pie animation at the top of the README.

It plays the pie of docs/design/README.md: open, pick slots along the pick
line, open the Merge sub-pie on hover, go back through the centre and run
Extrude. Every part is simulated at 60 frames a second and written as SMIL
animations, which browsers play inside an <img>. Labels are Barlow outlines,
since an SVG shown as an image loads no fonts.

Needs fontTools with brotli for the .woff2: pip install fonttools brotli
"""

import math
from pathlib import Path

from draw import dot_svg, keys_svg, line_svg, pie_svg, pointer_svg
from glyphs import FONT
from pie import (
    GROUND,
    INK,
    LINE,
    LINE_START,
    ROOT_CENTRE,
    SIGNAL,
    STONE,
    Pie,
    clamp,
    ease_in_out,
    ease_out,
    lerp,
    mix,
)
from tracks import COLOUR, FPS, LOOP, POSITION, SHARE, TRACKS, put

HERE = Path(__file__).resolve().parent
OUT = HERE / "kompass-banner.svg"
WIDTH, HEIGHT = 1200, 640

# The starter pies in kompass/starter.json: label, bearing, opens a sub-pie.
MODELING = (
    "Modeling",
    [
        ("Extrude", 270, False),
        ("Bevel", 90, False),
        ("Knife", 180, False),
        ("Loop Cut", 0, False),
        ("Subdivide", 309, False),
        ("Inset", 51, False),
        ("Merge", 231, True),
        ("Snap", 129, True),
    ],
)
MERGE = (
    "Merge",
    [
        ("At Cursor", 270, False),
        ("Collapse", 90, False),
        ("By Distance", 180, False),
        ("At Center", 0, False),
        ("At First", 309, False),
        ("At Last", 51, False),
        ("Dissolve", 231, False),
        ("Fill", 129, False),
    ],
)

KEY_DOWN, KEY_UP = 0.5, 0.85
BACK_CLICK = 7.15
RUN_CLICK = 8.6


def moves(sub):
    """Return the pointer's moves as (start, end, Bezier points); sub is the
    centre the Merge sub-pie opens at."""
    sx, sy = sub
    return [
        (1.1, 1.7, [(600, 300), (650, 255), (730, 195), (765, 185)]),
        (2.1, 2.65, [(765, 185), (860, 195), (925, 255), (935, 312)]),
        (3.05, 3.95, [(935, 312), (950, 590), (600, 600), (440, 396)]),
        (
            4.45,
            5.0,
            [(sx, sy), (sx + 80, sy + 30), (sx + 170, sy + 20), (sx + 212, sy + 6)],
        ),
        (
            5.4,
            5.95,
            [
                (sx + 212, sy + 6),
                (sx + 170, sy - 90),
                (sx + 60, sy - 170),
                (sx + 24, sy - 186),
            ],
        ),
        (
            6.35,
            6.85,
            [
                (sx + 24, sy - 186),
                (sx + 20, sy - 120),
                (sx + 4, sy - 40),
                (sx + 2, sy - 2),
            ],
        ),
        (
            7.6,
            8.2,
            [(sx + 2, sy - 2), (sx - 10, sy - 50), (sx - 50, sy - 90), (372, 298)],
        ),
        (9.6, 10.6, [(372, 298), (430, 300), (540, 300), (600, 300)]),
    ]


def bezier(points, t):
    (ax, ay), (bx, by), (cx, cy), (dx, dy) = points
    u = 1 - t
    return (
        u**3 * ax + 3 * u * u * t * bx + 3 * u * t * t * cx + t**3 * dx,
        u**3 * ay + 3 * u * u * t * by + 3 * u * t * t * cy + t**3 * dy,
    )


def pointer_at(t, path):
    at = ROOT_CENTRE
    for start, end, points in path:
        if t < start:
            break
        at = bezier(points, ease_in_out(clamp((t - start) / (end - start))))
    return at


def simulate(path):
    """Run the loop once, recording every track; return the sub-pie's centre."""
    TRACKS.clear()
    root = Pie("root", MODELING, 1.0)
    sub = Pie("sub", MERGE, 0.72)
    dt = 1 / FPS
    frames = round(LOOP * FPS)
    sub_centre = None
    clicks = []
    for frame in range(frames + 1):
        t = frame * dt
        p = pointer_at(t, path)
        if abs(t - KEY_DOWN) < dt / 2:
            root.open(ROOT_CENTRE, p)
        if abs(t - BACK_CLICK) < dt / 2:
            clicks.append(t)
            sub.to_ghost(sub.centre, 0.88)
            root.open(ROOT_CENTRE, p)
            root.suppress = 6
        if abs(t - RUN_CLICK) < dt / 2:
            clicks.append(t)
            root.mode = "closing"

        active = sub if sub.mode == "open" else root if root.mode == "open" else None
        if active is root and root.step(p, dt):
            sub_centre = p
            root.to_ghost(p, 0.9)
            sub.open(p, p)
            sub.angle = root.angle
            active = sub
        elif active is sub:
            sub.step(p, dt)

        for pie in (root, sub):
            pie.advance(dt)
            pie.record()
        record_line(active, p)
        record_pointer(p, t, clicks)
        keys = 1.0 if KEY_DOWN <= t < KEY_UP else 0.0
        put("keys-stroke", mix(LINE, SIGNAL, keys), COLOUR)
        put("keys-text", mix(STONE, INK, keys), COLOUR)
    return sub_centre


def record_line(pie, p):
    shown = pie is not None and math.dist(p, pie.centre) > pie.dial + LINE_START
    if shown:
        a = pie.line_start(p)
        g = ease_out(pie.red)
        c = pie.contact
        red_a = (lerp(c[0], a[0], g), lerp(c[1], a[1], g))
        red_b = (lerp(c[0], p[0], g), lerp(c[1], p[1], g))
        fade = ease_out(pie.open_share)
    else:
        a = red_a = red_b = c = p
        g = fade = 0.0
    put("line-op", fade, SHARE)
    for name, q in (("a", a), ("b", p), ("ra", red_a), ("rb", red_b)):
        put(f"line-{name}x", q[0], POSITION)
        put(f"line-{name}y", q[1], POSITION)
    put("line-red-op", 1.0 if g > 0 else 0.0, SHARE)
    put("dot-at", c, POSITION)
    put("dot-op", g * fade, SHARE)


def record_pointer(p, t, clicks):
    put("pointer-at", p, POSITION)
    since = min((t - c for c in clicks if c <= t), default=9.0)
    pressed = since < 0.12
    put("pointer-s", 0.88 if pressed else 1.0, SHARE / 4)
    ring = clamp(since / 0.35)
    put("ripple-r", lerp(4, 22, ease_out(ring)), POSITION)
    put("ripple-op", 0.0 if since >= 0.35 else 0.7 * (1 - ring), SHARE)


def main():
    planned = (440, 396)
    actual = simulate(moves(planned))
    actual = simulate(moves(actual))
    root, sub = Pie("root", MODELING, 1.0), Pie("sub", MERGE, 0.72)
    body = "".join(
        [keys_svg(), line_svg(), pie_svg(root), pie_svg(sub), dot_svg(), pointer_svg()]
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" role="img" aria-label="Kompass pie menu in use">'
        f"<defs>{FONT.defs()}</defs>"
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="12" fill="{GROUND}"/>'
        f"{body}</svg>\n"
    )
    OUT.write_text(svg)
    print(
        f"{OUT.name}: {len(svg) / 1024:.0f} KB, sub-pie at {actual[0]:.0f}, {actual[1]:.0f}"
    )


if __name__ == "__main__":
    main()
