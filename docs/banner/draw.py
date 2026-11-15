# SPDX-License-Identifier: GPL-3.0-or-later
"""The SVG of each part, its moving attributes taken from the tracks."""

import math

from glyphs import FONT
from pie import (
    INK,
    LABEL_SIZE,
    LINE,
    NEEDLE_INSET,
    SIGNAL,
    SLOT_HEIGHT,
    STONE,
    WHITE,
)
from tracks import element, num, transformed


def dial_svg(pie):
    k = pie.key
    r = pie.dial
    # pathLength 360 makes dash lengths degrees: one tick per 5 or 45 degrees.
    minor = 360 / (2 * math.pi * (r - 2.5))
    major = 2 * 360 / (2 * math.pi * (r - 6))
    needle = pie.dial - NEEDLE_INSET
    half = 6 * pie.k + 2
    ticks = []
    for i, slot in enumerate(pie.slots):
        bearing = round(slot["bearing"] / 5) * 5
        ticks.append(
            element(
                "line",
                {
                    "x1": 0,
                    "y1": num(-r + 5),
                    "x2": 0,
                    "y2": num(-r),
                    "stroke": SIGNAL,
                    "stroke_width": 3,
                    "transform": f"rotate({bearing})",
                },
                {"opacity": f"{k}-tick{i}-op"},
            )
        )
    return "".join(
        [
            transformed(f"{k}-dial-at", "translate"),
            transformed(f"{k}-dial-s", "scale"),
            f'<circle r="{num(r + 3)}" fill="none" stroke="{LINE}" stroke-width="1.5"/>',
            (
                f'<circle r="{num(r - 2.5)}" pathLength="360" fill="none" stroke="{STONE}" '
                f'stroke-opacity="0.55" stroke-width="5" stroke-dasharray="{num(minor, 3)} {num(5 - minor, 3)}" '
                f'stroke-dashoffset="{num(minor / 2, 3)}" transform="rotate(-90)"/>'
            ),
            element(
                "circle",
                {
                    "pathLength": 360,
                    "fill": "none",
                    "stroke": INK,
                    "stroke_dasharray": f"{num(major, 3)} {num(45 - major, 3)}",
                    "stroke_dashoffset": num(major / 2, 3),
                    "transform": "rotate(-90)",
                },
                {"r": f"{k}-major-r", "stroke-width": f"{k}-major-w"},
            ),
            *ticks,
            transformed(f"{k}-angle", "rotate"),
            transformed(f"{k}-arrow-at", "translate"),
            transformed(f"{k}-arrow-s", "scale"),
            element(
                "path",
                {"d": "M0 -4l5 8h-10z", "fill": SIGNAL},
                {"opacity": f"{k}-arrow-op"},
            ),
            "</g></g>",
            transformed(f"{k}-needle-s", "scale"),
            element(
                "g",
                {},
                {"opacity": f"{k}-needle-op"},
                f'<path d="M0 {num(-needle)}L{num(half)} -3H{num(-half)}Z" fill="{SIGNAL}"/>'
                f'<path d="M{num(-half)} 3H{num(half)}L0 {num(needle)}Z" fill="{INK}"/>',
            ),
            "</g></g>",
            element(
                "circle",
                {"fill": SIGNAL, "stroke": WHITE},
                {"r": f"{k}-disc-r", "stroke-width": f"{k}-disc-w"},
            ),
            "</g></g>",
        ]
    )


def slot_svg(pie, i):
    k = pie.key
    slot = pie.slots[i]
    w, h = slot["w"], SLOT_HEIGHT
    x, y = -w / 2, -h / 2
    parts = [
        transformed(f"{k}-slot{i}-at", "translate"),
        transformed(f"{k}-s", "scale"),
        element(
            "rect",
            {"x": num(x), "y": num(y), "width": w, "height": h, "stroke_width": 1},
            {"fill": f"{k}-slot{i}-fill", "stroke": f"{k}-slot{i}-stroke"},
        ),
    ]
    if slot["sub"]:
        parts += [
            element(
                "rect",
                {"y": num(y), "height": h, "fill": SIGNAL},
                {"x": f"{k}-slot{i}-wipe-x", "width": f"{k}-slot{i}-wipe"},
            ),
            element(
                "rect",
                {
                    "x": num(x + 0.5),
                    "y": num(y + 0.5),
                    "width": w - 1,
                    "height": h - 1,
                    "fill": "none",
                    "stroke": SIGNAL,
                },
                {"opacity": f"{k}-slot{i}-edge"},
            ),
            element(
                "path",
                {"d": f"M{num(-x - 9)} {num(y)}H{num(-x)}V{num(y + 9)}Z"},
                {"fill": f"{k}-slot{i}-mark"},
            ),
        ]
    label = FONT.label(slot["label"], LABEL_SIZE, 0.08, 0, LABEL_SIZE * 0.36)
    parts.append(element("g", {}, {"fill": f"{k}-slot{i}-text"}, label))
    parts.append("</g></g>")
    return "".join(parts)


def pie_svg(pie):
    k = pie.key
    title = FONT.label(pie.name.upper(), 12, 0.14, 0, 4)
    hint = FONT.label("BACK" if k == "sub" else "CLOSE", 11, 0.12, 0, 4)
    return element(
        "g",
        {},
        {"opacity": f"{k}-op"},
        "".join(
            [
                dial_svg(pie),
                transformed(f"{k}-title-at", "translate"),
                transformed(f"{k}-s", "scale"),
                f'<g fill="{INK}">{title}</g></g></g>',
                transformed(f"{k}-hint-at", "translate"),
                transformed(f"{k}-s", "scale"),
                element(
                    "g", {}, {"fill": f"{k}-hint-fill", "opacity": f"{k}-hint-op"}, hint
                ),
                "</g></g>",
                *(slot_svg(pie, i) for i, _ in enumerate(pie.slots)),
            ]
        ),
    )


def keys_svg():
    out, x = [], 40
    for key in ("SHIFT", "ALT", "Q"):
        w = max(34, FONT.width(key, 13, 0.1) + 22)
        out.append(
            element(
                "rect",
                {
                    "x": x,
                    "y": 584,
                    "width": num(w),
                    "height": 28,
                    "rx": 4,
                    "fill": "none",
                    "stroke_width": 1.5,
                },
                {"stroke": "keys-stroke"},
            )
        )
        out.append(
            element(
                "g",
                {},
                {"fill": "keys-text"},
                FONT.label(key, 13, 0.1, x + w / 2, 603),
            )
        )
        x += w + 8
    return "".join(out)


def line_svg():
    dashed = element(
        "line",
        {"stroke": STONE, "stroke_width": 1.5, "stroke_dasharray": "4 4"},
        {"x1": "line-ax", "y1": "line-ay", "x2": "line-bx", "y2": "line-by"},
    )
    red = element(
        "line",
        {"stroke": SIGNAL, "stroke_width": 1.5},
        {
            "x1": "line-rax",
            "y1": "line-ray",
            "x2": "line-rbx",
            "y2": "line-rby",
            "opacity": "line-red-op",
        },
    )
    return element("g", {}, {"opacity": "line-op"}, dashed + red)


def dot_svg():
    return (
        transformed("dot-at", "translate")
        + element("circle", {"r": 3.5, "fill": WHITE}, {"opacity": "dot-op"})
        + "</g>"
    )


def pointer_svg():
    arrow = (
        f'<path d="M0 0V17.5L4.4 13.4L7.3 20.2L10.2 19L7.3 12.3H13Z" fill="{WHITE}" '
        f'stroke="#000" stroke-width="1.2" stroke-linejoin="round"/>'
    )
    ripple = element(
        "circle",
        {"fill": "none", "stroke": WHITE, "stroke_width": 1.5},
        {"r": "ripple-r", "opacity": "ripple-op"},
    )
    return (
        transformed("pointer-at", "translate")
        + ripple
        + transformed("pointer-s", "scale")
        + arrow
        + "</g></g>"
    )
